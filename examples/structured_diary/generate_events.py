import random
from datetime import date, datetime, timedelta
from random import choice
import cltl.g2kmore.thought_util as util
from cltl.brain.long_term_memory import LongTermMemory
import os
from pathlib import Path
from cltl.commons.discrete import Certainty, Polarity, Sentiment, Emotion, GoEmotion


locations = ["chidos", "labas", "living_room", "vu", "carls_home", "carlas_home", "hospital", "bridge_club", "health_center", "dentist_center"]
activities = ["doctor", "dentist", "swimming", "walking","gym", "lunch", "breakfast", "dinner", "shopping", 'cooking', "cleaning", "washing", "visit", "reading", "watch_tv", "bridge"]
friends = ["carla", "fred", "john", "mary"]
certainties = [0, 0.2, 0.5, 0.7, 1]
sentiments = [-1, -0.7, -0.5, 0.2, 0, 0.2, 0.5, 0.7, 1]
polarities = [0, 0.5, 1]
emotions = [GoEmotion.DISAPPOINTMENT, GoEmotion.JOY, GoEmotion.ANGER, GoEmotion.AMUSEMENT, GoEmotion.APPROVAL, GoEmotion.ANNOYANCE, GoEmotion.CONFUSION, GoEmotion.DISAPPROVAL, GoEmotion.DISGUST, GoEmotion.EXCITEMENT]

def create_an_event(human:str, event_date:datetime):
    location = choice(locations)
    activity = choice(activities)
    friend = choice(friends)
    # certainty = choice(certainties)
    # sentiment = choice(sentiments)
    # polarity = choice(polarities)
    # emotion= choice(emotions)

    certainty = random.randint(0, Certainty.__len__()-1)
    sentiment = random.randint(0, Sentiment.__len__()-1)
    polarity = random.randint(0, Polarity.__len__()-1)
   # emotion = random.randint(0, GoEmotion.__len__()-1)
    emotion = random.randint(0, Emotion.__len__()-1)

    event_data = {
        "time": event_date,
        "location": location,
        "activity_label": activity,
        "activity_type": "icf",
        "actor1": human,
        "actor2": friend,
        "author": human,
        "author_uri": "http://cltl.nl/leolani/n2mu/" + human,
        "perspective": {"certainty": certainty,
                        "sentiment": sentiment,
                        "emotion":emotion,
                        "polarity": polarity
                        }
    }
    return event_data

def create_a_life(human: str, start: date, end: date, leap:int, nr:int):
    life = []
    event_date = start
    while event_date<end:
        nr_events = random.randint(1, nr)
        for i in range(nr_events):
            event_data = create_an_event(human, event_date)
            life.append(event_data)
        ### jump in time some days random from deltas
        days = random.randint(1, leap)
        event_date = event_date+timedelta(days=days)
    return life


if __name__ == "__main__":
    end = datetime(2024, 3, 12)
    start = datetime(2023, 12, 5)
    life = create_a_life(human = "carl", start=start, leap=2, end=end, nr=2)
    print(life)
    activity = life[0]
    capsule = util.make_activity_capsule_for_perspective(1, 1,
                                                         activity['activity_label'],
                                                         "",
                                                         activity['activity_type'],
                                                         activity['author'],
                                                         activity['author_uri'],
                                                         activity['perspective'])
    print(capsule)

    log_path = "log_path"
    if not os.path.exists(log_path):
        dir = os.mkdir(log_path)
    brain = LongTermMemory(address="http://localhost:7200/repositories/demo",
                           log_dir=Path(log_path), clear_all=False)

    brain.capsule_mention(capsule, reason_types=False, return_thoughts=False, create_label=True)
