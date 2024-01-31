import logging
import random

from cltl.brain.utils.helper_functions import brain_response_to_json
from cltl.combot.event.bdi import IntentionEvent, Intention
from cltl.combot.infra.config import ConfigurationManager
from cltl.combot.infra.event import Event, EventBus
from cltl.combot.infra.resource import ResourceManager
from cltl.combot.infra.topic_worker import TopicWorker
from cltl.commons.discrete import UtteranceType

logger = logging.getLogger(__name__)


class ThoughtIntentionService:
    @classmethod
    def from_config(cls, event_bus: EventBus, resource_manager: ResourceManager, config_manager: ConfigurationManager):
        config = config_manager.get_config("cltl.thought_intentions")
        g2km_ratio = config.get_float("g2km_ratio")

        config = config_manager.get_config("cltl.thought_intentions.events")
        input_topic = config.get("topic_input")
        output_topic = config.get("topic_output") if "topic_output" in config else None
        intention_topic = config.get("topic_intention")

        return cls(g2km_ratio, input_topic, output_topic, intention_topic, event_bus, resource_manager)

    def __init__(self, g2km_ratio: float, input_topic: str, output_topic: str, intention_topic: str,
                 event_bus: EventBus, resource_manager: ResourceManager):
        self._event_bus = event_bus
        self._resource_manager = resource_manager

        self._g2km_ratio = g2km_ratio

        self._input_topic = input_topic
        self._output_topic = output_topic
        self._intention_topic = intention_topic

        self._topic_worker = None
        self._active = False

    @property
    def app(self):
        return None

    def start(self, timeout=30):
        self._topic_worker = TopicWorker([self._input_topic, self._intention_topic],
                                         self._event_bus, provides=[self._output_topic],
                                         resource_manager=self._resource_manager, processor=self._process,
                                         name=self.__class__.__name__)
        self._topic_worker.start().wait()

    def stop(self):
        if not self._topic_worker:
            pass

        self._topic_worker.stop()
        self._topic_worker.await_stop()
        self._topic_worker = None

    def _process(self, event: Event):
        if event.metadata.topic == self._intention_topic and hasattr(event.payload, "intentions"):
            if any(intention.label == "chat" for intention in event.payload.intentions):
                self._active = True
            return

        if not self._active:
            return

        brain_responses = [brain_response_to_json(brain_response) for brain_response in event.payload]
        statements = [capsule for capsule in brain_responses if
                      ('statement' in capsule
                       and 'utterance_type' in capsule['statement']
                       and capsule['statement']['utterance_type'] == UtteranceType.STATEMENT.name)]

        gap = self._get_gap_target(statements)
        if gap and random.random() < self._g2km_ratio:
            intention = Intention("g2kmore", gap)
            self._event_bus.publish(self._intention_topic, Event.for_payload(IntentionEvent([intention])))
            self._active = False
            logger.info("Set intention to %s from brain responses", intention)
        elif self._output_topic:
            self._event_bus.publish(self._output_topic, Event.for_payload(event.payload))
            logger.info("Forwarded brain responses")


    def _get_gap_target(self, statements):
        gaps = [statement['thoughts'][gap_type]
                for statement in statements
                for gap_type in ['_subject_gaps', '_complement_gaps']
                if ('thoughts' in statement
                    and gap_type in statement['thoughts']
                    and statement['thoughts'][gap_type])
                and statement['thoughts'][gap_type]]

        entities = [entity["_known_entity"]
                    for gap in gaps
                    for entity_type in ["_subject", "_complement"]
                    for entity in gap[entity_type]]

        targets = list({(entity["_label"], entity["_types"][0])
                   for entity in entities
                   if entity["_label"] and entity['_types']})

        logger.debug("Choosing target from %s", targets)

        return random.choice(targets) if targets else None