import random
from datetime import date, datetime, timedelta
from random import choice
import cltl.g2kmore.thought_util as util
from cltl.brain.long_term_memory import LongTermMemory
import os
from pathlib import Path
from cltl.commons.discrete import Certainty, Polarity, Sentiment, Emotion, GoEmotion
from enum import Enum, auto
import get_temporal_containers as query


##### Predefined items to pick from
locations = ["chidos", "labas", "living_room", "city centre",  "VU", "carl_home", "carla_home", "hospital", "club", "health_center"]
activities = ["doctor", "school", "dancing", "dentist", "hair", "museum", "swim", "walk","gym", "lunch", "breakfast", "dinner", "shop", 'cook', "clean", "wash", "visit", "read", "tv", "bridge"]
friends = ["carla", "fred", "john", "mary", "peter", "jorge", "suzy"]

#sentiments = [-1, -0.9, -0.8, -0.7, -0.6, -0.5, -0.4, -0.3, -0.2, -0.1, 0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]

class GoNegEmotion(Enum):
    FEAR = auto()
    NERVOUSNESS = auto()
    REMORSE = auto()
    EMBARRASSMENT = auto()
    DISAPPOINTMENT = auto()
    SADNESS = auto()
    GRIEF = auto()
    DISGUST = auto()
    ANGER = auto()
    ANNOYANCE = auto()
    DISAPPROVAL = auto()
    REALIZATION = auto()
    CONFUSION = auto()

    @staticmethod
    def random():
        emotion= choice(list(GoNegEmotion))
        return emotion.name

class GoPosEmotion(Enum):
    AMUSEMENT = auto()
    EXCITEMENT = auto()
    JOY = auto()
    LOVE = auto()
    DESIRE = auto()
    OPTIMISM = auto()
    CARING = auto()
    PRIDE = auto()
    ADMIRATION = auto()
    GRATITUDE = auto()
    RELIEF = auto()
    APPROVAL = auto()
    SURPRISE = auto()
    CURIOSITY = auto()

    @staticmethod
    def random():
        emotion = choice(list(GoPosEmotion))
        return emotion.name

def create_an_event(human:str, event_date:datetime, activity_type):
    location = choice(locations)
    activity = choice(activities)
    friend = choice(friends)
    i = choice(range(6,20)) ### pick a random hour
    updated_time = event_date + timedelta(hours=i)
    certainty = choice(list(Certainty))
       # random.randint(1, Certainty.__len__()-1)
    sentiment = choice(list(Sentiment))
    polarity = choice(list(Polarity))
    emotion = GoEmotion.NEUTRAL
    if sentiment.value < -0.2:
        emotion = GoNegEmotion.random()
    elif sentiment.value > 0.2:
        emotion = GoPosEmotion.random()
    event_data = {
        "time": updated_time,
        "location": location,
        "activity_label": activity,
        "activity_type": activity_type,
        "actor1": human,
        "actor2": friend,
        "author": human,
        "author_uri": "http://cltl.nl/leolani/n2mu/" + human,
        "perspective": {"certainty": certainty,
                        "sentiment": sentiment,
                        "emotion": emotion,
                        "polarity": polarity
                        }
    }
    #print('event_data', sentiment, emotion)
    return event_data

def create_a_life(human: str, start: date, end: date, leap:int, nr:int, activity_type="activity"):
    life = []
    event_date = start
    while event_date<end:
        nr_events = random.randint(1, nr)
        for i in range(nr_events):
            event = create_an_event(human, event_date, activity_type=activity_type)
            life.append(event)
        ### jump in time some days random from deltas
        days = random.randint(1, leap)
        event_date = event_date+timedelta(days=days)
    return life


if __name__ == "__main__":
    log_path = "log_path"
    if not os.path.exists(log_path):
        dir = os.mkdir(log_path)
    brain = LongTermMemory(address="http://localhost:7200/repositories/demo",
                           log_dir=Path(log_path), clear_all=False)
    current_date = datetime(2024, 2, 15)

    end = datetime(2024, 3, 12)
    start = datetime(2023, 12, 5)
    life = create_a_life(human = "carl", start=start, leap=2, end=end, nr=2, activity_type="icf")
    util.add_activities_to_ekg(brain, current_date=current_date, activities=life)
    # for activity in life:
    #    capsule = util.make_activity_capsule(1, 1, activity['activity_label'],
    #                                                      "",
    #                                                      activity['activity_type'],
    #                                                      activity['author'],
    #                                                      activity['author_uri'],
    #                                                      activity['perspective'])
        #print(capsule)
    #   brain.capsule_mention(capsule, reason_types=False, return_thoughts=False, create_label=True)


    activity_tpe = "n2mu:icf"
    activity_query = util.get_all_instances_query(activity_tpe)
    brain_response = brain._submit_query(activity_query)
    print('I found', len(brain_response), 'activities')


    # #### We can simulate another day as now!
    # target = "carl"
    # current_date = datetime(2024, 1, 11)
    # PREVIOUS_DATE = datetime(2024,1, 2)
    # FUTURE_PERIOD = datetime(2024, 2, 29)
    # recent_date = query.get_last_conversation_date(target, brain, current_date, PREVIOUS_DATE)
    # history, gap, future, unknown = query.get_temporal_containers(brain, current_date, recent_date)
    #
    # #print(brain_response)
    # for activity in brain_response:
    #     activity_id = activity["id"]["value"]
    #     activity_label= activity["label"]["value"]
    #     event_perspectives = [] #### To be fixed when properly stored in the eKG
    #     print(activity_id)
    #     # Get the perspectives from the brain when it works
    #     query = util.get_perspective_query(activity_id)
    #     #print('perspective query', query)
    #     perspective_response = brain._submit_query(query)
    #     for p in perspective_response:
    #         perspective = p['perspective_value']['value']
    #         perspective = perspective[perspective.rindex("#")+1:]
    #         if not perspective=="UNDERSPECIFIED":
    #             event_perspectives.append(perspective)
    #     print('event_perspectives', event_perspectives)