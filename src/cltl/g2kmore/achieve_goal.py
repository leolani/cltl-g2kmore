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
from datetime import date, datetime
from random import getrandbits
from cltl.commons.discrete import UtteranceType
from cltl.brain.utils.helper_functions import brain_response_to_json

logger = logging.getLogger(__name__)

mention = {
                    "chat": 1,
                    "turn": 1,
                    "author": {"label": "lenka", "type": ["person"],
                               'uri': "http://cltl.nl/leolani/friends/lenka"},
                    "utterance": "",
                    "utterance_type": UtteranceType.TEXT_MENTION,
                    "position": "",
                    "item": {'label': 'piek', 'type': ['person'],
                             'uri': ""},
                    "timestamp": datetime.now(),
                    "context_id": 1
                }
statement = {
                    "chat": 1,
                    "turn": 1,
                    "author": {"label": "lenka", "type": ["person"],
                               'uri': "http://cltl.nl/leolani/friends/lenka"},
                    "utterance": "",
                    "utterance_type": UtteranceType.STATEMENT,
                    "position": "",
                    "subject": {"label": "piek", "type": ["person"],
                                "uri": ""},
                    "predicate": {"label": "be-from", "uri": "http://cltl.nl/leolani/n2mu/be-from"},
                    "object": {"label": "amsterdam", "type": ["location"],
                               "uri": "http://cltl.nl/leolani/world/amsterdam"},
                    "item": {'label': 'piek', 'type': ['person'],
                             'uri': ""},
                    "timestamp": datetime.now(),
                    "context_id": 1
                }

class ConvState(enum.Enum):
    START = 1
    QUERY = 2
    CONFIRM = 3
    REACHED = 4

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
    def __init__(self):
        self._state = State(ConvState.START)
        self._goal = None
        self._status = None
        self._attempts = 0

    @property
    def state(self) -> State:
        return self._state

    def triple_to_string(self, triple):
        say = "\t("
        if "subject" in triple:
            say += triple["subject"]["label"]
        say += ", "
        if "predicate" in triple:
            say += triple["predicate"]["label"]
        say += ", "
        if "object" in triple:
            say += triple["object"]["label"]
        say += ")"
        return say

    def print_goal(self, goal):
        for gap in goal:
            g = gap["triple"]
            say = self.triple_to_string(g)
            print(say)

    def get_subject_gaps (self, subject):
        subject_gaps = []
        #### get all subject gaps from the eKG for a specific subject
        #### should this be a label of a uri?
        return subject_gaps

    def get_object_gaps (self, object):
        object_gaps = []
        #### get all object gaps from the eKG for a specific object
        #### should this be a label of a uri?
        return object_gaps

    def is_subject_gap_filled(self, triple_g, triple_s):
        subject_match = triple_g["subject"]["label"]==triple_s["subject"]["label"]
        predicate_match = triple_g["predicate"]["label"]==triple_s["predicate"]["label"]
        if subject_match and predicate_match and "object" in triple_s:
            if triple_s["object"]["label"]=="":
                return None
            else:
                return triple_s["object"]
        else:
            return None

    def is_object_gap_filled(self, triple_s, triple_g):
        predicate_match = triple_g["predicate"]["label"]==triple_s["predicate"]["label"]
        object_match = triple_g["object"]["label"]==triple_s["object"]["label"]
        if object_match and predicate_match and "subject" in triple_s:
            return triple_s["subject"]
        else:
            return None

    def has_gap (self, gap, goals):
        for g in goals:
            gap_string = self.triple_to_string(gap)
            g_string = self.triple_to_string(g["triple"])
            if gap_string==g_string:
                return True
        return False

    def goal_check(self, goal, status):
        new_goal = []
        achievements =[]
        for triple_s in status:
            for gap in goal:
                thought = gap["thought"]
                triple_g = gap["triple"]
                if not self.is_subject_gap_filled(triple_g, triple_s):
                    if not self.has_gap(triple_g, new_goal):
                        new_goal.append(gap)
                elif not triple_s in achievements:
                    achievements.append(triple_s)
        return new_goal, achievements

    def get_triples_from_question_responses(self, responses):
        triples = []
        for subgoal in responses:
            triple = self.get_triple_from_question(subgoal['question'])
            if 'subject' in triple and 'predicate' in triple and 'object' in triple:
                triples.append(triple)
        return triples

    def get_triple_from_thought_subject(self, thought_subject):
        #     {"_known_entity": {"_id": "http://cltl.nl/leolani/world/lenka-1", "_label": "lenka", "_offset": null,
        #                        "_confidence": 0.0, "_types": ["person", "Instance"]},
        #      "_predicate": {"_id": "http://cltl.nl/leolani/n2mu/be-ancestor-of", "_label": "be-ancestor-of",
        #                     "_offset": null, "_confidence": 0.0, "_cardinality": 1},,
        #      "_entity": {"_id": "http://cltl.nl/leolani/n2mu/", "_label": "", "_offset": null, "_confidence": 0.0, "_types": ["person"]}},
        triple = {}
        if "_known_entity" in thought_subject:
            triple['subject'] = self.get_thought_value(thought_subject["_known_entity"])
        if "_predicate" in thought_subject:
            triple['predicate'] = self.get_thought_value(thought_subject["_predicate"])
        if "_entity" in thought_subject:
            triple['object'] = self.get_thought_value(thought_subject["_entity"])
        return triple

    def get_thought_value(self, element):
        value = {}
        if "_id" in element:
            value["uri"] = element["_id"]
        if "_label" in element:
            value["label"] = element["_label"]
        if "_types" in element:
            value["type"] = element["_types"]
        return value

    def get_triple_from_question(self, goal):
        triple = {}
        if "subject" in goal:
            triple['subject'] = goal['subject']
        if "predicate" in goal:
            triple['predicate'] = goal['predicate']
        if "object" in goal:
            triple['object'] = goal['object']
        return triple

    def get_triple_from_question_triple(self, goal):
        triple = {}
        if "_subject" in goal['triple']:
            triple['subject'] = goal['triple']['_subject']
        if "_predicate" in goal['triple']:
            triple['predicate'] = goal['triple']['_predicate']
        if "_object" in goal['triple']:
            triple['object'] = goal['triple']['_object']
        return triple

    def get_gaps_from_thought_response(self, responses):
        # "_subject_gaps":
        # {"_subject": [
        #     {"_known_entity": {"_id": "http://cltl.nl/leolani/world/lenka-1", "_label": "lenka", "_offset": null,
        #                        "_confidence": 0.0, "_types": ["person", "Instance"]},
        #      "_predicate": {"_id": "http://cltl.nl/leolani/n2mu/be-ancestor-of", "_label": "be-ancestor-of",
        #                     "_offset": null, "_confidence": 0.0, "_cardinality": 1},
        #      "_entity": {"_id": "http://cltl.nl/leolani/n2mu/", "_label": "", "_offset": null, "_confidence": 0.0,
        #                  "_types": ["person"]}},

        # {"_complement": [1
        #     { "_entity": {"_id": "http://cltl.nl/leolani/n2mu/", "_label": "", "_offset": null, "_confidence": 0.0, "_types": ["person"]}},

        #      "_predicate": {"_id": "http://cltl.nl/leolani/n2mu/be-ancestor-of", "_label": "be-ancestor-of",
        #                     "_offset": null, "_confidence": 0.0, "_cardinality": 1},
        #       "_known_entity": {"_id": "http://cltl.nl/leolani/world/lenka-1", "_label": "lenka", "_offset": null,
        #                   #                        "_confidence": 0.0, "_types": ["person", "Instance"]},

        gaps = []
        for response in responses:
            if 'thoughts' in response:
                print('thoughts', response['thoughts'])
                if "_subject_gaps" in response['thoughts'] and "_subject" in response['thoughts']['_subject_gaps']:
                    print(response['thoughts']['_subject_gaps'])
                    for thought in response['thoughts']['_subject_gaps']["_subject"]:
                        gap={}
                        gap["thought"]=thought
                        triple = self.get_triple_from_thought_subject(thought)
                        gap["triple"]=triple
                        gaps.append(gap)
                    for thought in response['thoughts']['_subject_gaps']["_complement"]:
                        gap={}
                        gap["thought"]=thought
                        triple = self.get_triple_from_thought_subject(thought)
                        gap["triple"]=triple
                        gaps.append(gap)
                if "_complement_gaps" in response['thoughts'] and "_subject" in response['thoughts']['_complement_gaps']:
                    print(response['thoughts']['_complement_gaps'])
                    for thought in response['thoughts']['_complement_gaps']["_subject"]:
                        gap={}
                        gap["thought"]=thought
                        triple = self.get_triple_from_thought_subject(thought)
                        gap["triple"]=triple
                        gaps.append(gap)
                    for thought in response['thoughts']['_complement_gaps']["_complement"]:
                        gap={}
                        gap["thought"]=thought
                        triple = self.get_triple_from_thought_subject(thought)
                        gap["triple"]=triple
                        gaps.append(gap)
        #print(gaps)
        return gaps

    def aim_for_goal(self, goal_thought_triples, brain, replier) -> Optional[str]:
        logger.debug("Received a goal %s in state %s", goal_thought_triples, self.state.conv_state.name)
        goal_thought_triples=goal_thought_triples[:5]
        ### Goal check

        graph_status = []
        if goal_thought_triples:
            for gap in  goal_thought_triples:
                #### check the graph
                triple = gap["triple"]
                response = brain.query_brain(triple)
                if response:
                    graph_status.append(response)
                else:
                    print('No response from eKG', triple)
        else:
            print("No goal triples detected.")
            self._state = ConvState.REACHED
            return

        print(graph_status)
        status_triples= self.get_triples_from_question_responses(graph_status)

        # print('goal_triples', len(goal_triples), goal_triples)
        # print('status_triples', len(status_triples))

        ### we got the current status of the eKG
        ### the new goal is determined by checking this
        new_goals, achievements = self.goal_check(goal_thought_triples, status_triples)
        print('goal', len(goal_thought_triples))
        self.print_goal(goal_thought_triples)
        print('achievements', len(achievements))
        self.print_goal(achievements)
        print('new_goals', len(new_goals))
        self.print_goal(new_goals)

        ### if there is a new_goal, we are generating replies for all subgoals
        if new_goals:
            self._goal = new_goals

            reply = "NO REPLY GENERATED"
            gap = {}
            while reply == "NO REPLY GENERATED":
            # for gap in tqdm(new_goals):
                gap = random.choice(list(new_goals))
            ## fix _subject and _complement choice
                thought = {"_subject_gaps": {"_subject": [gap["thought"]], "_complement": []}}
                ask = {"response": [], "statement": gap["triple"], "thoughts": thought}
                # reply = replier.reply_to_question(ask)
                reply = replier.reply_to_statement(ask, thought_options=["_subject_gaps"])
                self._attempts += 1
                if not reply:
                    reply = "NO REPLY GENERATED"
            # This is a text signal that needs to be posted to the event bus
            print(reply)
            # We now use the triple to fake a response from the user to resolve the gap:
            triple = gap["triple"]
            triple["predicate"]['label']=triple["predicate"]['label'].replace(" ", "-")
            triple["predicate"]['uri']=triple["predicate"]['uri'].replace(" ", "-")
            triple['object']['label']='piek'
            print('Triple for the faked user', self.triple_to_string(triple))
            capsule = self.make_capsule_from_triple(triple)
            response = brain.capsule_statement(capsule, reason_types=True, return_thoughts=True, create_label=True)
            print("response", response)


        else:
            #### We are done
            self.state.conv_state = ConvState.REACHED

        if self.state.conv_state == ConvState.START:
            response = "Tell me more!"
            self._state = self.state.transition(ConvState.QUERY)

    def response(self) -> Optional[str]:
        if self.state.conv_state == ConvState.START:
            self._state = self.state.transition(ConvState.QUERY)

            return "Hi, nice to meet you! What is your name?"

        return None

    def clear(self):
        self._state = self._state.transition(ConvState.START)

    def make_capsule_from_triple(selfs, triple):
        capsule = {"chat": 1,
                   "turn": 1,
                   "author": {"label": "lenka", "type": ["person"],
                              'uri': "http://cltl.nl/leolani/friends/lenka"},
                   "utterance": "",
                   "utterance_type": UtteranceType.STATEMENT,
                   "position": "",
                   ###
                   "subject": triple['subject'],
                   "predicate": triple['predicate'],
                   "object": triple['object'],
                   ###
                   "context_id": 1,
                   "timestamp": datetime.now()
                   }
        return capsule

if __name__ == "__main__":
    goal_file = "../../../examples/data/basic-questions-responses.json"
    goal_file = "../../../examples/data/thoughts-responses.json"
    log_path = "log_path"
    if not os.path.exists(log_path):
        dir = os.mkdir(log_path)
    f = open(goal_file, )
    goal = json.load(f)
    # Create brain connection
    brain = LongTermMemory(address="http://localhost:7200/repositories/sandbox",
                           log_dir=Path(log_path),
                           clear_all=False)
    #### Get thoughts about topic
    goal =[brain_response_to_json(brain.capsule_mention(mention))]
    response = brain.capsule_statement(statement, reason_types=True, return_thoughts=True, create_label=False)
    goal =[brain_response_to_json(response)]

    replier = LenkaReplier()
    g2km = GetToKnowMore()
    goals = g2km.get_gaps_from_thought_response(goal)
    g2km.aim_for_goal(goals, brain, replier)