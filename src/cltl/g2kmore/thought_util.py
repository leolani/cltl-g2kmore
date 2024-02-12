from datetime import date, datetime
from cltl.commons.discrete import UtteranceType
from random import getrandbits

from cltl.commons.discrete import UtteranceType

context_id, place_id, start_date = getrandbits(8), getrandbits(8), date.today() #(2017, 10, 24)


n2mu = "http://cltl.nl/leolani/n2mu/"
sem = "http://semanticweb.cs.vu.nl/2009/11/sem/"
leolaniworld = "http://cltl.nl/leolani/world/"

def make_context():
    context = {"context_id": context_id,
     "date": start_date,
     "place": "Piek's office",
     "place_id": place_id,
     "country": "Netherlands",
     "region": "North Holland",
     "city": "Amsterdam"}
    return context

def make_context(date):
    context = {"context_id": context_id,
     "date": date,
     "place": "Piek's office",
     "place_id": place_id,
     "country": "Netherlands",
     "region": "North Holland",
     "city": "Amsterdam"}
    return context

def make_target(target, type):
    mention = {
            "chat": 1,
            "turn": 1,
            "author": {"label": "dummy", "type": ["person"],
                       'uri': "http://cltl.nl/leolani/friends/dummy"},
            "utterance": "",
            "utterance_type": UtteranceType.TEXT_MENTION,
            "position": "0-25",
            "item": {'label': target, 'type': [type],
                     'uri': ""},
            "timestamp": datetime.now(),
            "context_id": context_id
    }
    return mention


def make_target_in_chat(chat, turn, target, type):
    mention = {
            "chat": chat,
            "turn": turn,
            "author": {"label": "dummy", "type": ["person"],
                       'uri': "http://cltl.nl/leolani/friends/dummy"},
            "utterance": "",
            "utterance_type": UtteranceType.TEXT_MENTION,
            "position": "0-25",
            "item": {'label': target, 'type': [type],
                     'uri': ""},
            "timestamp": datetime.now(),
            "context_id": context_id
    }
    return mention

def make_capsule_from_triple(triple):
    capsule = {"chat": 1,
               "turn": 1,
               "author": {"label": "dummy", "type": ["person"],
                          'uri': "http://cltl.nl/leolani/friends/dummy"},
               "utterance": "",
               "utterance_type": UtteranceType.STATEMENT,
               "position": "0-25",
               ###
               "subject": triple['subject'],
               "predicate": triple['predicate'],
               "object": triple['object'],
               "triple": triple,
               ###
               "context_id": 1,
               "timestamp": datetime.now()
               }
    return capsule

def add_activity_to_ekg(chat, turn, longterm_memory, activity_label, activity_id, activity_type, actor1=None, actor2=None, actor3=None, location=None, time=None,
                        author=None, author_uri=None, perspective=None):
    capsule = make_activity_capsule(chat, turn, activity_label, activity_id, activity_type, author, author_uri)
    longterm_memory.capsule_mention(capsule, reason_types=False, return_thoughts=False, create_label=True)
    if actor1:
        capsule = make_activity_capsule_with_actor(chat, turn, activity_label, activity_id, activity_type, author, author_uri, actor1)
        longterm_memory.capsule_statement(capsule, reason_types=False, return_thoughts=False, create_label=True)
    if actor2:
        capsule = make_activity_capsule_with_actor(chat, turn, activity_label, activity_id, activity_type, author, author_uri, actor2)
        longterm_memory.capsule_statement(capsule, reason_types=False, return_thoughts=False, create_label=True)
    if actor3:
        capsule = make_activity_capsule_with_actor(chat, turn, activity_label, activity_id, activity_type, author, author_uri, actor3)
        longterm_memory.capsule_statement(capsule, reason_types=False, return_thoughts=False, create_label=True)
    if location:
        capsule = make_activity_capsule_for_location(chat, turn, activity_label, activity_id, activity_type, author, author_uri, location)
        longterm_memory.capsule_statement(capsule, reason_types=False, return_thoughts=False, create_label=True)
    if time:
        capsule = make_activity_capsule_for_time(chat, turn, activity_label, activity_id, activity_type, author, author_uri, time)
        longterm_memory.capsule_statement(capsule, reason_types=False, return_thoughts=False, create_label=True)
    if perspective:
        capsule = make_activity_capsule_for_perspective(chat, turn, activity_label, activity_id, activity_type, author, author_uri, perspective)
        print(capsule)
        longterm_memory.capsule_mention(capsule, reason_types=False, return_thoughts=False, create_label=True)

def make_activity_capsule(chat, turn, activity, activity_id, activity_type, author, author_uri):
    capsule = {"chat": chat,
               "turn": turn,
               "author": {"label": author, "type": ["person"], 'uri': author_uri},

               "utterance": "",
               "utterance_type": UtteranceType.TEXT_MENTION,
               "position": "0-25",
               "item": {'label': activity, 'type': [activity_type], 'id': activity_id, 'uri': activity_id},
               "timestamp": datetime.combine(start_date, datetime.now().time()),
               "context_id": context_id
               }
    return capsule

def make_activity_capsule_for_perspective(chat, turn, activity, activity_id, activity_type, author, author_uri, perspective):
    capsule = {"chat": chat,
               "turn": turn,
               "author": {"label": author, "type": ["person"], 'uri': author_uri},

               "utterance": "",
               "utterance_type": UtteranceType.TEXT_MENTION,
               "position": "0-25",
               "item": {'label': activity, 'type': [activity_type], 'id': activity_id, 'uri': activity_id},
               "perspective": perspective,
               "timestamp": datetime.combine(start_date, datetime.now().time()),
               "context_id": context_id
               }
    return capsule

def make_activity_capsule_with_actor(chat, turn, activity, activity_id, activity_type, author, author_uri, actor):
    capsule = {"chat": chat,
               "turn": turn,
               "author": {"label": author, "type": ["person"], 'uri': author_uri},
               "utterance": "I think Lenka is from Serbia",
               "utterance_type": UtteranceType.STATEMENT,
               "position": "0-25",
               "subject": {"label": activity, "type": [activity_type], "uri": activity_id},
               "predicate": {"label": "actor", "uri": "sem:hasActor"},
               "object": {"label": actor, "type": ["person"],
                          "uri": ""},
               "timestamp": datetime.combine(start_date, datetime.now().time()),
               "context_id": context_id
               }
    return capsule

def make_activity_capsule_for_time(chat, turn, activity, activity_id, activity_type, author, author_uri, date):
    capsule = {"chat": chat,
               "turn": turn,
               "author": {"label": author, "type": ["person"], 'uri': author_uri},
               "utterance": "",
               "utterance_type": UtteranceType.STATEMENT,
               "position": "0-25",
               "subject": {"label": activity, "type": [activity_type], "uri": activity_id},
               "predicate": {"label": "actor", "uri": "sem:hasTime"},
               "object": {"label": str(date), "type": ["time"],
                          "uri": ""},
               "timestamp": datetime.combine(start_date, datetime.now().time()),
               "context_id": context_id
               }
    return capsule

def make_activity_capsule_for_location(chat, turn, activity, activity_id, activity_type, author, author_uri, location):
    capsule = {"chat": chat,
               "turn": turn,
               "author": {"label": author, "type": ["person"], 'uri': author_uri},
               "utterance": "",
               "utterance_type": UtteranceType.STATEMENT,
               "position": "0-25",
               "subject": {"label": activity, "type": [activity_type], "uri": activity_id},
               "predicate": {"label": "actor", "uri": "sem:hasPlace"},
               "object": {"label": location, "type": ["location"],
                          "uri": ""},
               "timestamp": datetime.combine(start_date, datetime.now().time()),
               "context_id": context_id
               }
    return capsule

def make_test_capsule_from_triple():
    capsule = {"chat": 2,
               "turn": 1,
               "author": {"label": "selene", "type": ["person"], 'uri': "http://cltl.nl/leolani/friends/selene-1"},
               "utterance": "I think Lenka is from Serbia",
               "utterance_type": UtteranceType.STATEMENT,
               "position": "0-25",
               "subject": {"label": "piek", "type": ["person"], "uri": ""},
               "predicate": {"label": "be-from", "uri": "http://cltl.nl/leolani/n2mu/be-from"},
               "object": {"label": "serbia", "type": ["location"],
                          "uri": ""},
               "perspective": {"certainty": 0.5,
                               "polarity": 1,
                               "sentiment": 0
                               },
               "timestamp": datetime.combine(start_date, datetime.now().time()),
               "context_id": context_id
               }
    return capsule

def remove_gap_from_goal(gap, goal):
    new_goal = []
    for g in goal:
        gap_string = triple_to_string(gap["triple"])
        g_string = triple_to_string(g["triple"])
        if not gap_string==g_string:
            new_goal.append(g)
    return new_goal

def triple_to_string(triple):
    say = "\t("
    if "subject" in triple:
        if "label" in triple["subject"]:
            say += triple["subject"]["label"]
        else:
            say += triple["subject"]
    say += ", "
    if "predicate" in triple:
        if "label" in triple["predicate"]:
            say += triple["predicate"]["label"]
        else:
            say += triple["predicate"]
    say += ", "
    if "object" in triple:
        if not type(triple["object"]=="Timestamp"):
            if "label" in triple["object"]:
                say += triple["object"]["label"]
            else:
                say += triple["object"]
        else:
            say += str(triple["object"])
    say += ")"
    return say

def print_goal(goal):
    for gap in goal:
        g = gap["triple"]
        say = triple_to_string(g)
        print(say)

def get_subject_gaps (subject):
    subject_gaps = []
    #### get all subject gaps from the eKG for a specific subject
    #### should this be a label of a uri?
    return subject_gaps

def get_object_gaps (object):
    object_gaps = []
    #### get all object gaps from the eKG for a specific object
    #### should this be a label of a uri?
    return object_gaps

def is_subject_gap_filled(triple_g, triple_s):
    subject_match = triple_g["subject"]["label" ]==triple_s["subject"]["label"]
    predicate_match = triple_g["predicate"]["label" ]==triple_s["predicate"]["label"]
    if subject_match and predicate_match and "object" in triple_s:
        if triple_s["object"]["label" ]=="":
            return None
        else:
            return triple_s["object"]
    else:
        return None

def is_object_gap_filled(triple_s, triple_g):
    predicate_match = triple_g["predicate"]["label" ]==triple_s["predicate"]["label"]
    object_match = triple_g["object"]["label" ]==triple_s["object"]["label"]
    if object_match and predicate_match and "subject" in triple_s:
        return triple_s["subject"]
    else:
        return None

def has_gap (gap, goals):
    for g in goals:
        gap_string = triple_to_string(gap)
        g_string = triple_to_string(g["triple"])
        if gap_string==g_string:
            return True
    return False

def goal_check(goal, status):
    new_goal = []
    achievements =[]
    for triple_s in status:
        for gap in goal:
            thought = gap["thought"]
            triple_g = gap["triple"]
            if not is_subject_gap_filled(triple_g, triple_s):
                if not has_gap(triple_g, new_goal):
                    new_goal.append(gap)
            elif not triple_s in achievements:
                achievements.append(triple_s)
    return new_goal, achievements

def make_event_query_for_date(triple):
    query = "select ?event where { \
            ?event sem:hasTime "
    query += triple["object"]["uri"] + ". }"
    return query

def get_triples_from_question_responses(responses):
    triples = []
    for subgoal in responses:
        triple = get_triple_from_question(subgoal['question'])
        if 'subject' in triple and 'predicate' in triple and 'object' in triple:
            triples.append(triple)
    return triples


def get_triple_from_thought_subject(thought_subject):
    #     {"_known_entity": {"_id": "http://cltl.nl/leolani/world/lenka-1", "_label": "lenka", "_offset": null,
    #                        "_confidence": 0.0, "_types": ["person", "Instance"]},
    #      "_predicate": {"_id": "http://cltl.nl/leolani/n2mu/be-ancestor-of", "_label": "be-ancestor-of",
    #                     "_offset": null, "_confidence": 0.0, "_cardinality": 1},,
    #      "_entity": {"_id": "http://cltl.nl/leolani/n2mu/", "_label": "", "_offset": null, "_confidence": 0.0, "_types": ["person"]}},
    triple = {}
    if "_known_entity" in thought_subject:
        triple['subject'] = get_thought_value(thought_subject["_known_entity"])
    if "_predicate" in thought_subject:
        triple['predicate'] = get_thought_value(thought_subject["_predicate"])
    if "_entity" in thought_subject:
        triple['object'] = get_thought_value(thought_subject["_entity"])
    return triple


def get_thought_value(element):
    value = {}
    if "_id" in element:
        value["uri"] = element["_id"]
    if "_label" in element:
        value["label"] = element["_label"]
    if "_types" in element:
        value["type"] = element["_types"]
    return value


def get_triple_from_question(goal):
    triple = {}
    if "subject" in goal:
        triple['subject'] = goal['subject']
    if "predicate" in goal:
        triple['predicate'] = goal['predicate']
    if "object" in goal:
        triple['object'] = goal['object']
    return triple


def get_triple_from_question_triple(goal):
    triple = {}
    if "_subject" in goal['triple']:
        triple['subject'] = goal['triple']['_subject']
    if "_predicate" in goal['triple']:
        triple['predicate'] = goal['triple']['_predicate']
    if "_object" in goal['triple']:
        triple['object'] = goal['triple']['_object']
    return triple

def get_event_gaps_for_period(period:[]):
    #    ?event <sem:hasTime> leolaniWorld:2024-01-10_00:00:00 .
    gaps = []
    for date in period:
        gap = {"count": 1}
        thought= {}
        thought["_known_entity"]={'id': leolaniworld+str(date).replace(" ", "_"), '_types': [], '_label': str(date)}
        thought["_predicate"]={'id': sem+'hasTime', '_types': [], '_label': 'hasTime'}
        thought["_entity"]={'id': 'http://cltl.nl/leolani/n2mu/', '_types': ['event'], '_label': ''}
        gap["thought"] = thought
        triple = {}
        triple['subject'] = {'uri': '', 'type': [], 'label': ""}
        triple['predicate'] = {'uri': sem+'hasTime', 'label': "hasTime"}
        triple['object'] = {"uri": leolaniworld+str(date).replace(" ", "_"), 'type': [], 'label': str(date)}
        gap["triple"] = triple
        gaps.append(gap)
    return gaps
#
# {'count': 1, 'thought': {'_known_entity': {'_id': 'http://cltl.nl/leolani/world/carl', '_label': 'carl', '_offset': None, '_confidence': 0.0, '_types': ['person', 'Instance']},
# '_predicate': {'_id': 'http://cltl.nl/leolani/n2mu/be-ancestor-of', '_label': 'be-ancestor-of', '_offset': None, '_confidence': 0.0, '_cardinality': 1},
# '_entity': {'_id': 'http://cltl.nl/leolani/n2mu/', '_label': '', '_offset': None, '_confidence': 0.0, '_types': ['person']}},
# 'triple': {'subject': {'uri': 'http://cltl.nl/leolani/world/carl', 'label': 'carl', 'type': ['person', 'Instance']},
# 'predicate': {'uri': 'http://cltl.nl/leolani/n2mu/be-ancestor-of', 'label': 'be-ancestor-of'},
# 'object': {'uri': 'http://cltl.nl/leolani/n2mu/', 'label': '', 'type': ['person']}}},
#

def get_gaps_from_thought_response(responses):
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
            if "_subject_gaps" in response['thoughts'] and not response['thoughts']['_subject_gaps']==None and "_subject" in response['thoughts']['_subject_gaps']:
                for thought in response['thoughts']['_subject_gaps']["_subject"]:
                    gap = {"count": 1}
                    gap["thought"] = thought
                    triple = get_triple_from_thought_subject(thought)
                    gap["triple"] = triple
                    gaps.append(gap)
                for thought in response['thoughts']['_subject_gaps']["_complement"]:
                    gap = {}
                    gap["thought"] = thought
                    triple = get_triple_from_thought_subject(thought)
                    gap["triple"] = triple
                    gaps.append(gap)
            if "_complement_gaps" in response['thoughts'] and not response['thoughts']['_complement_gaps']==None and "_subject" in response['thoughts']['_complement_gaps']:
                for thought in response['thoughts']['_complement_gaps']["_subject"]:
                    gap = {"count": 1}
                    gap["thought"] = thought
                    triple = get_triple_from_thought_subject(thought)
                    gap["triple"] = triple
                    gaps.append(gap)
                for thought in response['thoughts']['_complement_gaps']["_complement"]:
                    gap = {"count": 1}
                    gap["thought"] = thought
                    triple = get_triple_from_thought_subject(thought)
                    gap["triple"] = triple
                    gaps.append(gap)
    # print(gaps)
    return gaps


def get_all_utterances(target):
    query = "PREFIX n2mu: <http://cltl.nl/leolani/n2mu/> \
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\
            PREFIX dc: <http://purl.org/dc/elements/1.1/>\
            PREFIX grasp: <http://groundedannotationframework.org/grasp#>\
            PREFIX prov: <http://www.w3.org/ns/prov#>\
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\
            PREFIX sem: <http://semanticweb.cs.vu.nl/2009/11/sem/>\
            PREFIX time: <http://www.w3.org/TR/owl-time/#>\
            PREFIX leolaniTalk: <http://cltl.nl/leolani/talk/>\
            select ?context ?utterance ?actor ?year ?month ?day where { \
                GRAPH leolaniTalk:Interactions { \
                    ?context sem:hasEvent ?e .\
                    ?context ?p ?t .\
                    ?t time:day ?day .\
                    ?t time:month ?month .\
                    ?t time:year ?year .\
                    ?e rdf:type sem:Event, grasp:Chat .\
                    ?e sem:hasSubEvent ?utterance .\
                    ?utterance sem:hasActor ?actor . \
                    ?actor rdfs:label "
    query += '\"' + target + '\" .'
    query += '}}'
    return query


def get_all_instances(type):
    query = "PREFIX n2mu: <http://cltl.nl/leolani/n2mu/>\
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\
            select ?id ?label where {\
                ?id rdf:type " + type + ". \
                ?id rdfs:label ?label . \
                }"
    return query

def get_sem_relations(event_id):
        query = "PREFIX n2mu: <http://cltl.nl/leolani/n2mu/>\
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\
                PREFIX sem: <http://semanticweb.cs.vu.nl/2009/11/sem/>\
                select ?actor_id ?place_id ?time_id where { \
                { \
                    { <" + event_id +  "> <sem:hasActor> ?actor_id} UNION \
                    { <" + event_id +  "> <sem:hasPlace> ?place_id} UNION \
                    { <" + event_id +  "> <sem:hasTime> ?time_id} \
                } \
            } "
        return query

def get_perspectives(event_id):
    query = "PREFIX n2mu: <http://cltl.nl/leolani/n2mu/>\
            PREFIX grasp: <http://groundedannotationframework.org/grasp#>\
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\
            PREFIX gaf: <http://groundedannotationframework.org/gaf#>\
            select ?event_id ?perspective_value where \
            { <" + event_id + "> <http://groundedannotationframework.org/gaf#denotedIn> ?utterance_id . \
            ?utterance_id <http://groundedannotationframework.org/grasp#hasAttribution> ?att. \
            ?att rdf:value  ?perspective_value.}"
    return query



def know_about_target_subject(target):
    query = "PREFIX n2mu: <http://cltl.nl/leolani/n2mu/> \
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> \
            PREFIX dc: <http://purl.org/dc/elements/1.1/> \
            select ?s ?p ?ol where { \
                ?s ?p ?o . \
                ?s rdfs:label "
    query += '\"'+target+'\" .'
    query +='    ?o rdfs:label ?ol . \
                FILTER( STRSTARTS(str(?p), str(n2mu:))) \
            }'
    return query


def know_about_target_object(target):
    query = "PREFIX n2mu: <http://cltl.nl/leolani/n2mu/> \
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> \
            PREFIX dc: <http://purl.org/dc/elements/1.1/> \
            select ?sl ?p ?o where { \
                ?s ?p ?o . \
                ?o rdfs:label "
    query += '\"'+target+'\" .'
    query +='    ?s rdfs:label ?sl . \
                FILTER( STRSTARTS(str(?p), str(n2mu:))) \
            }'
    return query