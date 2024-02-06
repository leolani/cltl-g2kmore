import json
import random
from datetime import date, datetime, timedelta
from random import choice

locations = ["chidos", "labas", "living_room", "vu", "carls_home", "carlas_home", "hospital", "bridge_club", "health_center", "dentist_center"]
activities = ["doctor", "dentist", "swimming", "walking","gym", "lunch", "breakfast", "dinner", "shopping", 'cooking', "cleaning", "washing", "visit", "reading", "watch_tv", "bridge"]
friends = ["carla", "fred", "john", "mary"]
certainties = [0, 0.2, 0.5, 0.7, 1]
sentiments = [-1, -0.7, -0.5, 0.2, 0, 0.2, 0.5, 0.7, 1]
polarities = [0, 0.5, 1]

def create_a_life(human: str, start: date, end: date, leap:int, nr:int):
    life = []
    event_date = start
    while event_date<end:
        nr_events = random.randint(1, nr)
        for i in range(nr_events):
            location = choice(locations)
            activity = choice(activities)
            friend = choice(friends)
            certainty = choice(certainties)
            sentiment = choice(sentiments)
            polarity = choice(polarities)
            activity_data = {
            "time": event_date,
            "location": location,
            "activity_label": activity,
            "activity_type": "icf",
            "actor1": human,
            "actor2": friend,
             "author": human,
            "author_uri": "http://cltl.nl/leolani/n2mu/"+human,
            "perspective": {"certainty": certainty,
                            "sentiment": sentiment,
                            "polarity": polarity
                        }
            }
            life.append(activity_data)
        ### jump in time some days random from deltas
        days = random.randint(1, leap)
        event_date = event_date+timedelta(days=days)
    return life


if __name__ == "__main__":
    end = datetime(2024, 3, 12)
    start = datetime(2023, 12, 5)
    life = create_a_life(human = "carl", start=start, leap=int, end=end, nr=2)
    print(life)