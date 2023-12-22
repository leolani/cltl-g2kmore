import dataclasses
import logging
import uuid
from typing import Union, List, Iterable

from cltl.combot.event.bdi import DesireEvent
from cltl.combot.event.emissor import TextSignalEvent, AnnotationEvent
from cltl.combot.infra.config import ConfigurationManager
from cltl.combot.infra.event import Event, EventBus
from cltl.combot.infra.resource import ResourceManager
from cltl.combot.infra.time_util import timestamp_now
from cltl.combot.infra.topic_worker import TopicWorker
from cltl.combot.infra.groupby_processor import GroupProcessor, Group, GroupByProcessor
from cltl.nlp.api import Entity, EntityType
from cltl.vector_id.api import VectorIdentity
from cltl_service.emissordata.client import EmissorDataClient
from emissor.representation.scenario import TextSignal, Mention, Annotation, Signal, MultiIndex

from cltl.g2kmore.api import GetToKnowMore

logger = logging.getLogger(__name__)

class GetToKnowMoreService(Group):
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

        return cls(config.get("topic_utterance"),
                   config.get("topic_id"), config.get("topic_response"), config.get("topic_speaker"),
                   intention_topic, desire_topic, intentions,
                   g2kmore, emissor_client, event_bus, resource_manager)

    def __init__(self, utterance_topic: str, id_topic: str, response_topic: str,
                 speaker_topic: str, intention_topic: str, desire_topic: str, intentions: List[str],
                 g2kmore: GetToKnowMore, emissor_client: EmissorDataClient,
                 event_bus: EventBus, resource_manager: ResourceManager):
        self._g2kmore = g2kmore

        self._emissor_client = emissor_client
        self._event_bus = event_bus
        self._resource_manager = resource_manager
        self._utterance_topic = utterance_topic
        self._id_topic = id_topic
        self._response_topic = response_topic
        self._speaker_topic = speaker_topic
        self._intention_topic = intention_topic
        self._desire_topic = desire_topic
        self._intentions = intentions

        self._topic_worker = None
        self._app = None

    def start(self, timeout=30):
        topics = [self._utterance_topic, self._id_topic, self._intention_topic]
        self._topic_worker = TopicWorker(topics, self._event_bus,
                                         provides=[self._speaker_topic, self._response_topic],
                                         resource_manager=self._resource_manager,
                                         intention_topic=self._intention_topic, intentions=self._intentions,
                                         scheduled=1, buffer_size=16,
                                         processor=self._process, name=self.__class__.__name__)
        self._topic_worker.start().wait()

    def stop(self):
        if not self._topic_worker:
            pass

        self._topic_worker.stop()
        self._topic_worker.await_stop()
        self._topic_worker = None

    def _process(self, event: Event[Union[TextSignalEvent, AnnotationEvent]]):
        response = None
        if event is None or self._is_g2kmore_intention(event):
            response = self._g2kmore.response()
        elif event.metadata.topic == self._utterance_topic:
            response = self._g2kmore.utterance_detected(event.payload.signal.text)

        if response:
            response_payload = self._create_payload(response)
            self._event_bus.publish(self._response_topic, Event.for_payload(response_payload))

        id, name = self._g2kmore.speaker
        # TODO remember the right utterance
        if id and name and event and event.metadata.topic in [self._utterance_topic]:
            speaker_event = self._create_speaker_payload(event.payload.signal, id, name)
            self._event_bus.publish(self._speaker_topic, Event.for_payload(speaker_event))
            if self._desire_topic:
                self._event_bus.publish(self._desire_topic, Event.for_payload(DesireEvent(["resolved"])))

            self._g2kmore.clear()
            self._topic_worker.clear()

        if event:
            logger.debug("Found %s, %s, response: %s", id, name, response)

    def _is_g2kmore_intention(self, event):
        return (event.metadata.topic == self._intention_topic
                and hasattr(event.payload, "intentions")
                and 'g2kmore' in event.payload.intentions)

    def _create_payload(self, response):
        scenario_id = self._emissor_client.get_current_scenario_id()
        signal = TextSignal.for_scenario(scenario_id, timestamp_now(), timestamp_now(), None, response)

        return TextSignalEvent.for_agent(signal)

    # def _create_speaker_payload(self, signal: Signal, id, name):
    #     offset = signal.ruler
    #     if hasattr(signal, 'text'):
    #         segment_start = signal.text.find(name)
    #         if segment_start >= 0:
    #             offset = signal.ruler.get_offset(segment_start, segment_start + len(name))
    #
    #     ts = timestamp_now()
    #
    #     id_annotations = [Annotation(VectorIdentity.__name__, id, __name__, ts),
    #                       Annotation(Entity.__name__, Entity(name, EntityType.SPEAKER, offset), __name__, ts)]
    #
    #     return AnnotationEvent.create([Mention(str(uuid.uuid4()), [offset], id_annotations)])
