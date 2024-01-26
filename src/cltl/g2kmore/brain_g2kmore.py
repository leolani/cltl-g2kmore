import enum
import logging
import random
import copy
from typing import Optional, Union

from cltl.brain.utils.helper_functions import brain_response_to_json

import cltl.g2kmore.thought_util as util
from cltl.g2kmore.api import GetToKnowMore, ConvState

logger = logging.getLogger(__name__)


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
        self._state = ConvState.START
        self._goals = None
        self._achievements = []
        self._focus = None
        self._goal_attempts = 0
        self._goal_attempts_max = max_attempts
        self._focus_attempt_max = max_intention_attempts
        self._brain = brain

    @property
    def state(self) -> ConvState:
        self._evaluate()

        return self._state

    @property
    def intention(self) -> dict:
        return self._focus

    @property
    def desires(self) -> dict:
        return self._focus

    def set_target(self, target_label: str, target_type: str):
        brain_response = self._brain.capsule_mention(util.make_target(target_label, target_type),
                                               reason_types=True, return_thoughts=True, create_label=False)
        self.desires = util.get_gaps_from_thought_response([brain_response_to_json(brain_response)])

    @desires.setter
    def desires(self, desires: dict) -> None:
        self._goals = desires
        self._state = ConvState.START
        logger.debug("Set %s desires", len(self._goals))

        self._evaluate()

    def evaluate_and_act(self) -> Optional[Union[dict, str]]:
        self._evaluate()

        return self.get_action()

    def add_knowledge(self, capsule: dict):
        self._brain.capsule_statement(capsule, reason_types=True, return_thoughts=True, create_label=True)
        self._evaluate()

    def _evaluate(self):
        if self._state == ConvState.START:
            return

        if not self._goals:
            logger.debug("No goals left.")
            self._state = ConvState.REACHED
            return

        if self._goal_attempts > self._goal_attempts_max:
            self._state = ConvState.GIVEUP
            return

        if not self._focus:
            self._focus = random.choice(list(self._goals))
        elif self._focus["count"] > self._focus_attempt_max:
            logger.debug("Focus give up after attempts %s", self._focus["count"])
            self._focus = random.choice(list(self._goals))

        while achievement := self._evaluate_focus():
            logger.debug("We have a response: %s", achievement)
            logger.debug("We can shift focus")
            achievement.append(self._focus)
            self._achievements.append(achievement)

            self._goals = util.remove_gap_from_goal(self._focus, self._goals)
            if self._goals:
                self._focus = random.choice(list(self._goals))
            else:
                self._state = ConvState.REACHED
                return

    def _evaluate_focus(self):
        if not self._focus:
            return None

        logger.debug("Current focus is %s", util.triple_to_string(self._focus['triple']))
        triple = copy.deepcopy(self._focus["triple"])
        response = self._brain.query_brain(triple)
        if not response or not response["response"]:
            logger.debug('No response from eKG for triple %s', triple)
            logger.debug("No result for query. We keep the focus.")
            return None
        else:
            return response["response"]

    def get_action(self) -> Optional[Union[dict, str]]:
        self._evaluate()

        if self._state in [ConvState.START, ConvState.REACHED, ConvState.GIVEUP]:
            return self._response()
        else:
            return self._ask_more()

    def _ask_more(self):
        self._goal_attempts += 1

        if "count" not in self._focus:
            self._focus["count"] = 1
        else:
            self._focus["count"] += 1
        ask = None
        trying = 0
        while not ask and trying < 10:
            trying += 1
            # fix _subject and _complement choice
            thought = {"_subject_gaps": {"_subject": [self._focus["thought"]], "_complement": []}}
            ask = {"response": [], "statement": {"triple": self._focus["triple"]}, "thoughts": thought}

        logger.debug('Ask to get to know more: %s', ask)

        return copy.deepcopy(ask)

    def _response(self) -> Optional[str]:
        # response = self._brain._submit_query(util.know_about_target_subject(self._target))
        # response += self._brain._submit_query(util.know_about_target_object(self._target))
        #
        # logger.debug("This is what I know about %s: %s", self._target, response)
        if self._state == ConvState.START:
            self._state = ConvState.QUERY
            return "Hi, nice to meet you! What is your name?"
        elif self._state == ConvState.REACHED:
            logger.debug("ACHIEVEMENTS (%s attempts): %s ", self._goal_attempts, self._achievements)
            return "I am so happy"
        elif self._state == ConvState.GIVEUP:
            logger.debug("ACHIEVEMENTS (%s attempts): %s ", self._goal_attempts, self._achievements)
            return "This is all I could do! Sorry."

        return None
