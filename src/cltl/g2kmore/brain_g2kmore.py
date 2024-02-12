import enum
import logging
import random
import copy
from typing import Optional, Union, List

from cltl.brain.utils.helper_functions import brain_response_to_json

import cltl.g2kmore.thought_util as util
from cltl.g2kmore.api import GetToKnowMore, ConvState

logger = logging.getLogger(__name__)

n2mu = "http://cltl.nl/leolani/n2mu/"
sem = "http://semanticweb.cs.vu.nl/2009/11/sem/"
leolaniworld = "http://cltl.nl/leolani/world/"


class TripleStatus(enum.Enum):
    SUBJECTMATCH = 1
    PREDICATEMATCH = 2
    OBJECTMATCH = 3
    SUBJECTGAP = 4
    OBJECTGAP = 6
    PREDICATEGAP = 5


class BrainGetToKnowMore(GetToKnowMore):
    def __init__(self, brain, max_attempts=10, max_intention_attempts=3):
        self._target = None
        self._target_type = None
        self._state = ConvState.VOID
        self._desires = None
        self._achievements = []
        self._intention = None
        self._goal_attempts = 0
        self._goal_attempts_max = max_attempts
        self._intention_attempt_max = max_intention_attempts
        self._brain = brain

    @property
    def state(self) -> ConvState:
        self._evaluate()

        return self._state

    @property
    def intention(self) -> dict:
        return self._intention

    @property
    def desires(self) -> List[dict]:
        return self._desires

    @desires.setter
    def desires(self, desires: dict) -> None:
        self._desires = desires
        self._state = ConvState.START
        logger.debug("Set %s desires", len(self._desires))

        self._evaluate()

    @property
    def target(self):
        return (self._target, self._target_type)

    def set_target(self, target_label: str, target_type: str):
        self._target = target_label
        self._target_type = target_type
        brain_response = self._brain.capsule_mention(util.make_target(target_label, target_type),
                                               reason_types=True, return_thoughts=True, create_label=False)
        self.desires = util.get_gaps_from_thought_response([brain_response_to_json(brain_response)])
        self._state = ConvState.START
        logger.debug("Set target to %s[%s], set %s desires (%s)", self._target, self._target_type, len(self.desires), self._state)

    def set_target_events_for_period(self, target_label: str, target_type: str, period:[]):
        self._target = target_label
        self._target_type = target_type

        self.desires = util.get_event_gaps_for_period(period)

        self._state = ConvState.START
        logger.debug("Set target to %s[%s], set %s desires (%s)", self._target, self._target_type, len(self.desires), self._state)


    def evaluate_and_act(self) -> Optional[Union[dict, str]]:
        self._evaluate()

        return self.get_action()

    def add_knowledge(self, capsule: dict):
        self._brain.capsule_statement(capsule, reason_types=True, return_thoughts=True, create_label=True)
        self._evaluate()

    def _evaluate(self):
        if self._state in [ConvState.VOID, ConvState.START]:
            logger.debug("In initial state %s", self._state)
            return

        if not self._desires:
            logger.debug("No goals left.")
            self._state = ConvState.REACHED
            return

        if self._goal_attempts > self._goal_attempts_max:
            self._state = ConvState.GIVEUP
            return

        if not self._intention:
            self._intention = random.choice(list(self._desires))
            logger.debug("Set intention %s", self._intention['triple'])
        elif self._intention["count"] > self._intention_attempt_max:
            self._intention = random.choice(list(self._desires))
            logger.debug("intention give up after attempts %s, new intention %s", self._intention["count"], self._intention['triple'])

        while achievement := self._evaluate_intention():
            achievement.append(self._intention)
            self._achievements.append(achievement)

            self._desires = util.remove_gap_from_goal(self._intention, self._desires)
            logger.debug("Intention %s resolved", self._intention["triple"])
            if self._desires:
                self._intention = random.choice(list(self._desires))
                logger.debug("We shifted intention to %s", self._intention["triple"])
            else:
                self._state = ConvState.REACHED
                return

    def _evaluate_intention(self):
        if not self._intention:
            return None

        logger.debug("Current intention is %s", util.triple_to_string(self._intention['triple']))
        triple = copy.deepcopy(self._intention["triple"])
        response = self._brain.query_brain(triple)
        if not response or not response["response"]:
            logger.debug('No response from eKG for triple %s', triple)
            logger.debug("No result for query. We keep the intention.")
            return None
        else:
            logger.debug("We have a response: %s", response["response"])

            return response["response"]

    def _evaluate_event_intention(self):
        if not self._intention:
            return None

        logger.debug("Current intention is %s", util.triple_to_string(self._intention['triple']))
        triple = copy.deepcopy(self._intention["triple"])
        query = util.make_event_query_for_date(self, triple)
        # Perform query
        response = self._submit_query(query)
        # Create JSON output
        response = {'response': response, 'question': triple, 'rdf_log_path': None}

        if not response or not response["response"]:
            logger.debug('No response from eKG for triple %s', triple)
            logger.debug("No result for query. We keep the intention.")
            return None
        else:
            logger.debug("We have a response: %s", response["response"])

            return response["response"]

    def get_action(self) -> Optional[Union[dict, str]]:
        self._evaluate()

        logger.debug("Act in state %s with intention %s", self._state, self._intention['triple'] if self._intention else None)

        if self._state == ConvState.VOID:
            return None
        if self._state in [ConvState.START, ConvState.REACHED, ConvState.GIVEUP]:
            return self._response()
        else:
            return self._ask_more()

    def _ask_more(self):
        self._goal_attempts += 1

        if "count" not in self._intention:
            self._intention["count"] = 1
        else:
            self._intention["count"] += 1
        ask = None
        trying = 0
        while not ask and trying < 10:
            trying += 1
            # fix _subject and _complement choice
            thoughts = {
                "_statement_novelty": [],
                "_entity_novelty": [],
                "_negation_conflicts": [],
                "_complement_conflict": [],
                "_subject_gaps": {
                    "_subject": [self._intention["thought"]],
                    "_complement": []
                },
                "_complement_gaps": [],
                "_overlaps": [],
                "_trust": 0.5
            }
            ask = {
                "response": [],
                "statement": util.make_capsule_from_triple(self._intention["triple"]),
                "thoughts": thoughts
            }

        logger.debug('Ask to get to know more (%s): %s', trying, ask)

        return copy.deepcopy(ask)

    def _response(self) -> Optional[str]:
        # response = self._brain._submit_query(util.know_about_target_subject(self._target))
        # response += self._brain._submit_query(util.know_about_target_object(self._target))
        #
        # logger.debug("This is what I know about %s: %s", self._target, response)
        if self._state == ConvState.START:
            self._state = ConvState.QUERY
            return "I would like to know more about " + self._target
        elif self._state == ConvState.REACHED:
            logger.debug("ACHIEVEMENTS (%s attempts): %s ", self._goal_attempts, self._achievements)
            return "I am so happy"
        elif self._state == ConvState.GIVEUP:
            logger.debug("ACHIEVEMENTS (%s attempts): %s ", self._goal_attempts, self._achievements)
            return "This is all I could do! Sorry."
        else:
            raise ValueError("Illegal state " + self._state)

    def reset(self):
        self.__init__(self._brain, self._goal_attempts_max, self._intention_attempt_max)
