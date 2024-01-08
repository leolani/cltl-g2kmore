import dataclasses
import enum
import logging
import os
import random
from pathlib import Path
from typing import Optional

from cltl.brain.long_term_memory import LongTermMemory
from cltl.brain.utils.helper_functions import brain_response_to_json
from cltl.reply_generation.lenka_replier import LenkaReplier

import thought_util as util
from cltl.g2kmore.api import GetToKnowMore

logger = logging.getLogger(__name__)


class ConvState(enum.Enum):
    START = 1
    QUERY = 2
    CONFIRM = 3
    REACHED = 4
    GIVEUP = 5

    def transitions(self):
        return self._allowed[self]

    @property
    def _allowed(self):
        return {
            ConvState.START: [ConvState.QUERY],
            ConvState.QUERY: [ConvState.CONFIRM],
            ConvState.CONFIRM: [ConvState.REACHED, ConvState.QUERY],
            ConvState.REACHED: [ConvState.START]
        }


class TripleStatus(enum.Enum):
    SUBJECTMATCH = 1
    PREDICATEMATCH = 2
    OBJECTMATCH = 3
    SUBJECTGAP = 4
    PREDICATEGAP = 5
    OBJECTGAP = 6

    # @property
    # def _resolved(self):


@dataclasses.dataclass
class State:
    conv_state: Optional[ConvState]

    def transition(self, conv_state: ConvState, **kwargs):
        if conv_state not in self.conv_state.transitions():
            raise ValueError(f"Cannot change state from {self.conv_state} to {conv_state}")

        logger.debug("Transition from conversation state %s to %s", self.conv_state, conv_state)

        return self._transition(conv_state, **kwargs)

    def stay(self, **kwargs):
        logger.debug("Reenter conversation state %s to %s", self.conv_state)
        return self._transition(self.conv_state, **kwargs)

    def _transition(self, conv_state: ConvState, **kwargs):
        new_state = vars(State(None, None, None)) if conv_state == ConvState.START else vars(self)
        new_state.update(**kwargs)
        new_state["conv_state"] = conv_state

        return State(**new_state)


class GetToKnowMore(GetToKnowMore):
    def __init__(self, brain, replier):
        self._target = None
        self._target_type = None
        self._state = State(ConvState.START)
        self._goal = None
        self._achievements = []
        self._focus = None
        self._goal_attempts = 0
        self._goal_attempts_max = 5
        self._focus_attempt_max = 3
        self._brain = brain
        self._replier = replier

    @property
    def state(self) -> State:
        return self._state


    def _response(self) -> Optional[str]:
        response = self._brain._submit_query(util.know_about_target_subject(self._target))
        response += self._brain._submit_query(util.know_about_target_object(self._target))

        logger.debug("This is what I know about %s: %s", self._target, response)
        if self._state == ConvState.START:
            self._state = self.state.transition(ConvState.QUERY)
            return "Hi, nice to meet you! What is your name?"
        elif self._state == ConvState.REACHED:
            logger.debug("ACHIEVEMENTS", self._achievements)
            return "I am so happy"
        elif self._state == ConvState.GIVEUP:
            logger.debug("ACHIEVEMENTS", self._achievements)
            logger.debug("Attempts", self._goal_attempts)
            return "This is all I could do! Sorry."
        return None

    def clear(self):
        self._state = self._state.transition(ConvState.START)

    def _define(self, target, type):
        self._target = target
        self._target_type = type
        goal = [brain_response_to_json(self._brain.capsule_mention(util.make_target(target, type), reason_types=True, return_thoughts=True, create_label=False))]
        self._goal = util.get_gaps_from_thought_response(goal)
        logger.debug("Goal", len(self._goal), " gaps")
        self._state=ConvState.START

    def _evaluate(self):
        if self._goal==[]:
            logger.debug("No goals left.")
            self._state=ConvState.REACHED
            return
        elif self._goal_attempts > self._goal_attempts_max:
            self._state=ConvState.GIVEUP
            return
        if not self._focus:
            self._focus = random.choice(list(self._goal))
            self._goal_attempts += 1
        elif self._focus["count"] > self._focus_attempt_max:
            logger.debug("Focus give up after attempts", self._focus["count"])
            self._focus = random.choice(list(self._goal))
            self._goal_attempts += 1
        logger.debug("Current focus is", util.triple_to_string(self._focus['triple']))
        triple = self._focus["triple"]
        response = self._brain.query_brain(triple)
        if not response:
            logger.debug('No response from eKG', triple)
        else:
            if response["response"] == []:
                #### No result, keep focus
                logger.debug("No result for query. We keep the focus.")
            else:
                #### if response good, move focus from goal to achievent with response
                # set focus to None
                logger.debug("We have a response", response["response"])
                logger.debug("We can shift focus")
                self._goal = util.remove_gap_from_goal(self._focus, self._goal)
                achievement = response["response"]
                achievement.append(self._focus)
                self._achievements.append(achievement)
                self._focus = random.choice(list(self._goal))

    def _pursue(self):
        if not "count" in self._focus:
            self._focus["count"]=1
        else:
            self._focus["count"] +=1
        reply = "NO REPLY GENERATED"
        trying = 0
        while reply == "NO REPLY GENERATED" and trying < 10:
            trying +=1
            # for gap in tqdm(new_goals):
            ## fix _subject and _complement choice
            thought = {"_subject_gaps": {"_subject": [self._focus["thought"]], "_complement": []}}
            ask = {"response": [], "statement": self._focus["triple"], "thoughts": thought}
            reply = self._replier.reply_to_statement(ask, thought_options=["_subject_gaps"])
            if not reply:
                reply = "NO REPLY GENERATED"
        # This is a text signal that needs to be posted to the event bus
        logger.debug('Trying to get to know more', reply)
        return reply

    def _wait(self):
        ##### wait for a response for x seconds
        #### dummy respond
        # We now use the triple to fake a response from the user to resolve the gap:
        triple = self._focus["triple"]
        ### for some reason hyphens are lost in de predicates, hack to repair this
        triple["predicate"]['label'] = triple["predicate"]['label'].replace(" ", "-")
        triple["predicate"]['uri'] = triple["predicate"]['uri'].replace(" ", "-")
        ### We fill in a dummy as object to simulate new data for the eKG
        triple['object']['label'] = 'dummy'
        logger.debug('Triple as the fake user input', util.triple_to_string(triple))
        capsule = util.make_capsule_from_triple(triple)
        response = self._brain.capsule_statement(capsule, reason_types=True, return_thoughts=True, create_label=True)
        logger.debug("response pushing statement", response["response"])

    ## Main loop that 1) defines the task, pursues the goal, waits for an effect and evaluates the results
    ## Evaluating results adapts the goal
    ## pursue, wait, evaluate continues untill all goals are achieved or the attempts exceed the giveup threshold
    def _take_action(self, target, type)-> Optional[str]:
        logger.debug("Setting a goal for %s as a %s in state %s", target, type, self.state.conv_state.name)
        if self.state.conv_state == ConvState.START:
            response = "Tell me more!"
            self._state = self.state.transition(ConvState.QUERY)

        self._define(target, type)
        self._evaluate()

        while not self._state==ConvState.REACHED and not self._state==ConvState.GIVEUP:
            self._pursue()
            self._wait()
            self._evaluate()
            self._goal_attempts +=1

        say = self._response()
        logger.debug (say)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    # Create brain connection
    log_path = "log_path"
    if not os.path.exists(log_path):
        dir = os.mkdir(log_path)
    brain = LongTermMemory(address="http://localhost:7200/repositories/sandbox",
                           log_dir=Path(log_path),
                           clear_all=False)

    # testing the brain:
    # context = util.make_context()
    # response = brain.capsule_context(context)
    # logger.debug("response pushing context", response)
    #
    # capsule = util.make_capsule_from_triple()
    # response = brain.capsule_statement(capsule, reason_types=True, return_thoughts=True, create_label=False)
    # logger.debug("response pushing statement", response)

    replier = LenkaReplier()
    g2km = GetToKnowMore(brain, replier)
    ##### Settings for limits of goals to pursue and attempts
    g2km._goal_attempts_max = 10  # threshold for total goal attempts
    g2km._focus_attempt_max = 3  # threshold for each specific subgoal
    #### Get thoughts about target
    target = "piek"
    type = "person"
    g2km._take_action(target, type)


