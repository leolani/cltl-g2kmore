from datetime import datetime
from generate_events import create_a_life, create_an_event
import logging
import os
import pandas as pd
from pathlib import Path
import enum
import json
import get_temporal_containers as query
from cltl.brain.long_term_memory import LongTermMemory
from cltl.reply_generation.lenka_replier import LenkaReplier
import cltl.g2kmore.thought_util as util
from cltl.g2kmore.brain_g2kmore import BrainGetToKnowMore, ConvState
import visualise_timeline

logger = logging.getLogger(__name__)

n2mu = "http://cltl.nl/leolani/n2mu/"

#TODO integrate this with the way perspectives are store in the eKG
class Factuality(enum.Enum):
    REALIS = 1 # polarity: 1.0
    IRREALIS = 2 # polarity: 0.5
    DENIED = 3 # polarity: 0.0

def add_activity_to_ekg(brain: LongTermMemory, current_date, activities):
    #### We need to create a context for adding data to the eKG
    context = util.make_context()
    response = brain.capsule_context(context)
    #print("response pushing context", response)
    chat = str(current_date.timestamp())
    turn = "_1"

    for activity in activities:
       # print(activity)
        #### We add an activity
        if type(activity['time'])==datetime:
            event_date =activity['time']
        else:
            year = activity['time'][0]
            month = activity['time'][1]
            day = activity['time'][2]
            event_date = datetime(year, month, day)
        location =activity['location']
        activity_label = activity['activity_label']
        activity_uri = n2mu+activity['activity_label']+"_"+str(event_date.timestamp())
        activity_type = activity['activity_type']
        author = activity['author']
        author_uri = n2mu + author

        actor1 = None
        actor2 = None
        actor3 = None
        if 'actor1' in activity:
            actor1 = activity['actor1']
        if 'actor2' in activity:
            actor2 = activity['actor2']
        if 'actor3' in activity:
            actor3 = activity['actor3']

        perspective = None
        if 'pespective' in activity:
            perspective= activity['perspective']

        util.add_activity_to_ekg(chat, turn, brain, activity_label, activity_uri, activity_type,
                                 actor1=actor1, actor2=actor2, actor3=actor3,
                                 location=location,
                                 time=event_date,
                                 author=author,
                                 author_uri=author_uri,
                                 perspective=perspective)
if __name__ == "__main__":
    loaddata = False
    generatedata = False
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    log_path = "log_path"
    if not os.path.exists(log_path):
        dir = os.mkdir(log_path)
    brain = LongTermMemory(address="http://localhost:7200/repositories/demo",
                           log_dir=Path(log_path), clear_all=False)

    #TODO G2KMORE loop still needs to be implemented to ask for events or event properties
    ## We need to set the goal following the pseudocode for high leve beliefs, and middle and low level intents
    replier = LenkaReplier()
    g2km = BrainGetToKnowMore(brain, max_attempts=10, max_intention_attempts=3)

    event_type="icf"
    target = "carl"
    current_date = datetime.today()

    if loaddata:
        ##### Adding activity to the eKG
        activities_file = "data/activities-2.json"
        activities = json.load(open(activities_file))
        #add_activity_to_ekg(haydo._brain, current_date, activities)
        add_activity_to_ekg(brain, current_date, activities)
    elif generatedata:
        end = datetime(2024, 3, 4)
        start = datetime(2023, 12, 28)
        leap = 6
        life = create_a_life(human=target, start=start, end=end, leap=leap, nr=2)
        add_activity_to_ekg(brain, current_date, life)

    recent_date = query.get_last_conversation_date(target, brain, current_date)
    history, gap, future, unknown = query.get_temporal_containers(brain, current_date, recent_date)

    print('History before', recent_date, len(history), " activities")
    print("\t", history)
    print('Gap between', recent_date, " and ", current_date, len(gap), " activities")
    print("\t", gap)
    print('Future after', current_date, len(future), " activities")
    print("\t", future)
    print('Unknown date', len(unknown), ' activities')
    print("\t", unknown)

    story_of_life = history + gap + future
    visualise_timeline.create_timeline_image(story_of_life, target, current_date)

    gap_period = pd.date_range(recent_date.date(), current_date.date())

    g2km.set_target_events_for_period(target, event_type, gap_period)
    print("Set a goal for %s as a %s in state %s" % (target, event_type, g2km.state.name))

    while not g2km.state == ConvState.REACHED and not g2km.state == ConvState.GIVEUP:
        print('=======', g2km.state, '=======')
        # Reply is sometimes None as the replier randomly chooses between object and subject gaps
        response = g2km.evaluate_and_act()

        if not response:
            pass
        elif isinstance(response, str):
            print("Agent: ", response)
            print('User: Some user input as reply to', response)
        else:
            print("Agent: ", replier.reply_to_statement(response, thought_options=["_subject_gaps"]))

        print('intention', g2km._intention)
        # Wait for capsule event
        if g2km.state in [ConvState.QUERY]:
            event_date = g2km._intention["triple"]["object"]
            event = create_an_event(target, event_date)
            add_activity_to_ekg(brain, current_date, [event])
