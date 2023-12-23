import dataclasses
import enum
import logging
import random
import uuid
from typing import Optional, Tuple, Iterable, Mapping
from cltl.brain.long_term_memory import LongTermMemory
from cltl.reply_generation.lenka_replier import LenkaReplier
from cltl.g2kmore.api import GetToKnowMore
import json
from tqdm import tqdm
import os
from pathlib import Path
from cltl.brain.utils.helper_functions import brain_response_to_json
import thought_util as util

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
        self._state = State(ConvState.START)
        self._goal = None
        self._achievements = []
        self._focus = None
        self._status = None
        self._attempts = 0
        self._attemptsmax = 5
        self._hopeless = 3
        self._brain = brain
        self._replier = replier

    @property
    def state(self) -> State:
        return self._state


    def _response(self) -> Optional[str]:
        if self._state == ConvState.START:
            self._state = self.state.transition(ConvState.QUERY)
            return "Hi, nice to meet you! What is your name?"
        elif self._state == ConvState.REACHED:
            print("ACHIEVEMENTS", self._achievements)
            return "I am so happy"
        elif self._state == ConvState.GIVEUP:
            print("ACHIEVEMENTS", self._achievements)
            print("Attempts", self._attempts)
            return "This is all I could do! Sorry."
        return None

    def clear(self):
        self._state = self._state.transition(ConvState.START)

    def _define(self, target, type):
        goal = [brain_response_to_json(self._brain.capsule_mention(util.make_target(target, type), reason_types=True, return_thoughts=True, create_label=False))]
        self._goal = util.get_gaps_from_thought_response(goal)
        self._state=ConvState.START

    def _evaluate(self):
        if self._goal==[]:
            print("No goals left.")
            self._state=ConvState.REACHED
            return
        elif self._attempts > self._attemptsmax:
            self._state=ConvState.GIVEUP
            return
        if not self._focus:
            self._focus = random.choice(list(self._goal))
        elif self._focus["count"] > self._hopeless:
            print("Focus give up after attempts", self._focus["count"])
            self._focus = random.choice(list(self._goal))
        print("Current focus is", self._focus)
        triple = self._focus["triple"]
        response = self._brain.query_brain(triple)
        if not response:
            print('No response from eKG', triple)
        else:
            if response["response"] == []:
                #### No result, keep focus
                print("No result for query. We keep the focus.")
            else:
                #### if response good, move focus from goal to achievent with response
                # set focus to None
                print("We have a response", response["response"])
                print("We shift focus")
                self._goal = util.remove_gap_from_goal(self._focus, self._goal)
                achievement = response["response"]
                achievement.update(self._focus)
                self._achievements.append(achievement)
                self._focus = None

    def _pursui(self):
        self._focus["count"] +=1
        self._attempts += 1
        reply = "NO REPLY GENERATED"
        while reply == "NO REPLY GENERATED":
            # for gap in tqdm(new_goals):
            ## fix _subject and _complement choice
            thought = {"_subject_gaps": {"_subject": [self._focus["thought"]], "_complement": []}}
            ask = {"response": [], "statement": self._focus["triple"], "thoughts": thought}
            reply = self._replier.reply_to_statement(ask, thought_options=["_subject_gaps"])
            if not reply:
                reply = "NO REPLY GENERATED"
        # This is a text signal that needs to be posted to the event bus
        print(reply)
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
        print('Triple as the fake user input', util.triple_to_string(triple))
        capsule = util.make_capsule_from_triple(triple)
        response = self._brain.capsule_statement(capsule, reason_types=True, return_thoughts=True, create_label=True)
        print("response pushing statement", response)

    def _take_action(self, target, type)-> Optional[str]:
        logger.debug("Setting a goal for %s as a %s in state %s", target, type, self.state.conv_state.name)
        if self.state.conv_state == ConvState.START:
            response = "Tell me more!"
            self._state = self.state.transition(ConvState.QUERY)

        self._define(target, type)
        self._evaluate()

        while not self._state==ConvState.REACHED and not self._state==ConvState.GIVEUP:
            self._pursui()
            self._wait()
            self._evaluate()
            self._attempts +=1

        say = self._response()
        print (say)


if __name__ == "__main__":
    # Create brain connection

    log_path = "log_path"
    if not os.path.exists(log_path):
        dir = os.mkdir(log_path)
    brain = LongTermMemory(address="http://localhost:7200/repositories/sandbox2",
                           log_dir=Path(log_path),
                           clear_all=False)
    replier = LenkaReplier()
    g2km = GetToKnowMore(brain, replier)
    #### Get thoughts about target
    target = "piek"
    type = "person"
    g2km._take_action(target, type)




    ############

    ### Obsolete
    # def aim_for_goal(self, goal_thought_triples, brain, replier) -> Optional[str]:
    #     logger.debug("Setting a goal for %s as a %s in state %s", target, type, self.state.conv_state.name)
    #     goal_thought_triples=goal_thought_triples[:5]
    #     ### Goal check
    #
    #     graph_status = []
    #     if goal_thought_triples:
    #         for gap in  goal_thought_triples:
    #             #### check the graph
    #             triple = gap["triple"]
    #             response = brain.query_brain(triple)
    #             if response:
    #                 graph_status.append(response)
    #             else:
    #                 print('No response from eKG', triple)
    #     else:
    #         print("No goal triples detected.")
    #         self._state = ConvState.REACHED
    #         return
    #
    #     print(graph_status)
    #     status_triples= self.get_triples_from_question_responses(graph_status)
    #
    #     # print('goal_triples', len(goal_triples), goal_triples)
    #     # print('status_triples', len(status_triples))
    #
    #     ### we got the current status of the eKG
    #     ### the new goal is determined by checking this
    #     new_goals, achievements = self.goal_check(goal_thought_triples, status_triples)
    #     print('goal', len(goal_thought_triples))
    #     self.print_goal(goal_thought_triples)
    #     print('achievements', len(achievements))
    #     self.print_goal(achievements)
    #     print('new_goals', len(new_goals))
    #     self.print_goal(new_goals)
    #
    #     ### if there is a new_goal, we are generating replies for all subgoals
    #     if new_goals:
    #         self._goal = new_goals
    #
    #         reply = "NO REPLY GENERATED"
    #         gap = {}
    #         while reply == "NO REPLY GENERATED":
    #         # for gap in tqdm(new_goals):
    #             gap = random.choice(list(new_goals))
    #         ## fix _subject and _complement choice
    #             thought = {"_subject_gaps": {"_subject": [gap["thought"]], "_complement": []}}
    #             ask = {"response": [], "statement": gap["triple"], "thoughts": thought}
    #             # reply = replier.reply_to_question(ask)
    #             reply = replier.reply_to_statement(ask, thought_options=["_subject_gaps"])
    #             self._attempts += 1
    #             if not reply:
    #                 reply = "NO REPLY GENERATED"
    #         # This is a text signal that needs to be posted to the event bus
    #         print(reply)
    #         # We now use the triple to fake a response from the user to resolve the gap:
    #         triple = gap["triple"]
    #         triple["predicate"]['label']=triple["predicate"]['label'].replace(" ", "-")
    #         triple["predicate"]['uri']=triple["predicate"]['uri'].replace(" ", "-")
    #         triple['object']['label']='piek'
    #         print('Triple for the faked user', self.triple_to_string(triple))
    #         capsule = self.make_capsule_from_triple(triple)
    #         response = brain.capsule_statement(capsule, reason_types=True, return_thoughts=True, create_label=True)
    #         print("response", response)
    #
    #
    #     else:
    #         #### We are done
    #         self.state.conv_state = ConvState.REACHED
    #
    #     if self.state.conv_state == ConvState.START:
    #         response = "Tell me more!"
    #         self._state = self.state.transition(ConvState.QUERY)
