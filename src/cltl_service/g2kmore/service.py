import logging
from typing import Union, List

from cltl.combot.event.bdi import DesireEvent, IntentionEvent
from cltl.combot.event.emissor import TextSignalEvent, AnnotationEvent
from cltl.combot.infra.config import ConfigurationManager
from cltl.combot.infra.event import Event, EventBus
from cltl.combot.infra.groupby_processor import Group
from cltl.combot.infra.resource import ResourceManager
from cltl.combot.infra.time_util import timestamp_now
from cltl.combot.infra.topic_worker import TopicWorker
from cltl.commons.discrete import UtteranceType
from cltl_service.emissordata.client import EmissorDataClient
from emissor.representation.scenario import TextSignal

from cltl.g2kmore.api import GetToKnowMore, ConvState

logger = logging.getLogger(__name__)


class GetToKnowMoreService:
    """
    Service used to integrate the component into applications.
    """
    @classmethod
    def from_config(cls, g2kmore: GetToKnowMore, emissor_client: EmissorDataClient,
                    event_bus: EventBus, resource_manager: ResourceManager,
                    config_manager: ConfigurationManager):
        config = config_manager.get_config("cltl.g2kmore.events")

        intention_topic = config.get("topic_intention") if "topic_intention" in config else None
        desire_topic = config.get("topic_desire") if "topic_desire" in config else None
        intentions = config.get("intentions", multi=True) if "intentions" in config else []

        return cls(config.get("topic_knowledge"), config.get("topic_text_response"), config.get("topic_thought_response"),
                   intention_topic, desire_topic, intentions,
                   g2kmore, emissor_client, event_bus, resource_manager)

    def __init__(self, knowledge_topic: str, text_response_topic: str, thought_response_topic: str,
                 intention_topic: str, desire_topic: str, intentions: List[str],
                 g2kmore: GetToKnowMore, emissor_client: EmissorDataClient,
                 event_bus: EventBus, resource_manager: ResourceManager):
        self._g2kmore = g2kmore

        self._event_bus = event_bus
        self._emissor_client = emissor_client
        self._resource_manager = resource_manager

        self._knowledge_topic = knowledge_topic
        self._text_response_topic = text_response_topic
        self._thought_response_topic = thought_response_topic

        self._intention_topic = intention_topic
        self._desire_topic = desire_topic
        self._intentions = intentions

        self._topic_worker = None
        self._app = None

        self._last_response = None

    def start(self, timeout=30):
        topics = [self._knowledge_topic, self._intention_topic]
        self._topic_worker = TopicWorker(topics, self._event_bus,
                                         provides=[self._text_response_topic, self._thought_response_topic],
                                         resource_manager=self._resource_manager,
                                         intention_topic=self._intention_topic, intentions=self._intentions,
                                         scheduled=30, buffer_size=16,
                                         processor=self._process, name=self.__class__.__name__)
        self._topic_worker.start().wait()

    def stop(self):
        if not self._topic_worker:
            pass

        self._topic_worker.stop()
        self._topic_worker.await_stop()
        self._topic_worker = None

    def _process(self, event: Event):
        response = None
        if event is None:
            if self._g2kmore.state not in [ConvState.VOID, ConvState.REACHED, ConvState.GIVEUP]:
                response = "I would like to know more about " + self._g2kmore.target[0]
        elif self._is_g2kmore_intention(event):
            intention = next(intention for intention in event.payload.intentions if intention.label == "g2kmore")
            self._g2kmore.set_target(*intention.args)
            response = self._g2kmore.evaluate_and_act()
        elif (event.metadata.topic == self._knowledge_topic and
              any('statement' in capsule
                  and 'utterance_type' in capsule['statement']
                  and capsule['statement']['utterance_type'] == UtteranceType.STATEMENT
                  for capsule in event.payload)):
            response = self._g2kmore.evaluate_and_act()

        if isinstance(response, str):
            response_payload = self._create_text_payload(response)
            self._event_bus.publish(self._text_response_topic, Event.for_payload(response_payload))
        elif response:
            self._last_response = timestamp_now()
            self._event_bus.publish(self._thought_response_topic, Event.for_payload([response]))

        if self._g2kmore.state in [ConvState.REACHED, ConvState.GIVEUP]:
            if self._desire_topic:
                self._event_bus.publish(self._desire_topic, Event.for_payload(DesireEvent(["resolved"])))

            self._g2kmore.reset()
            self._topic_worker.clear()

    def _is_g2kmore_intention(self, event):
        return (event.metadata.topic == self._intention_topic
                and hasattr(event.payload, "intentions")
                and any('g2kmore' == intention.label for intention in event.payload.intentions))

    def _create_text_payload(self, response):
        scenario_id = self._emissor_client.get_current_scenario_id()
        signal = TextSignal.for_scenario(scenario_id, timestamp_now(), timestamp_now(), None, response)

        return TextSignalEvent.for_agent(signal)
