from datetime import datetime
from generate_events import create_a_life, create_an_event
import logging
import os
import pandas as pd
from pathlib import Path
import json
import get_temporal_containers as query
from cltl.brain.long_term_memory import LongTermMemory
from cltl.reply_generation.lenka_replier import LenkaReplier
import cltl.g2kmore.thought_util as util
from cltl.g2kmore.brain_g2kmore import BrainGetToKnowMore, ConvState

logger = logging.getLogger(__name__)

n2mu = "http://cltl.nl/leolani/n2mu/"
sem = "http://semanticweb.cs.vu.nl/2009/11/sem/"
leolaniworld = "http://cltl.nl/leolani/world/"
#
# #TODO integrate this with the way perspectives are stored in the eKG
# class Factuality(enum.Enum):
#     REALIS = 1 # polarity: 1.0
#     IRREALIS = 2 # polarity: 0.5
#     DENIED = 3 # polarity: 0.0

if __name__ == "__main__":
    loaddata = False
    generatedata = True
    density_threshold = 1.0
    saturation_threshold = 1.0

    activity_type="icf"
    target = "carla"
    current_date = datetime.today()
    #### We can simulate another day as now!
    current_date = datetime(2024, 2, 15)
    PREVIOUS_DATE = datetime(2024,2, 9)
    FUTURE_PERIOD = datetime(2024, 2, 29)


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


    if loaddata:
        ##### Adding activity to the eKG
        activities_file = "../data/activities-2.json"
        activities = json.load(open(activities_file))
        util.add_activities_to_ekg(brain, current_date, activities)
    elif generatedata:
        end = datetime(2024, 2, 20)
        start = datetime(2024, 2, 19)
        leap = 1
        life = create_a_life(human=target, start=start, end=end, leap=leap, nr=2, activity_type=activity_type)
        util.add_activities_to_ekg(brain, current_date, life)

    recent_date = query.get_last_conversation_date(target, brain, current_date, PREVIOUS_DATE)
    history, gap, future, unknown = query.get_temporal_containers(brain, current_date, recent_date)

    print('History before', recent_date, len(history), " activities")
    print("\t", history)
    print('Gap between', recent_date, " and ", current_date, len(gap), " activities")
    print("\t", gap)
    print('Future after', current_date, len(future), " activities")
    print("\t", future)
    print('Unknown date', len(unknown), ' activities')
    print("\t", unknown)

    ### The next code checks the density of events in the GAP period
    ### Density is average number of event per day for the GAP period
    ### If the density is equal or above the density threshold
    ###     We have enough acitvities registered
    ### Otherwise, we set a target goal for each day in the GAP period to ask for an event on that day
    ### This code then generates a new event as a response, which should be done by a dialog in the real system

    ### We first extract the list of dates that make up the GAP period
    gap_period = pd.date_range(recent_date.date(), current_date.date())
    print('The gap is', gap)

    ### For each event in the GAP, we need to check the realis, the saturation and the perspective
    for activity in gap:
        print(activity)
        #### getting more properties
        event_properties = util.get_sem_relation_query(activity['id'])
        if len(event_properties)>= saturation_threshold:
            print('I know enough', len(event_properties), 'saturation_threshold', saturation_threshold)
        else:
            #### ask for the properties
            print("Please tell me more about", activity["label"])
        perspectives = util.get_perspective_query("id")
        if not perspectives:
            print("Please tell me how was", activity["label"])
        else:
            print('Your perspective is', perspectives)

        #### get the missing perspectives
        #### ask for the perspective


    ### Here comes a for loop over the GAP events to ask for realis, saturation and perspective

    ### As far as we have not reached the density, we will add new events to the GAP
    density = len(gap)/len(gap_period)
    print('The current density is', density, len(gap), len(gap_period))
    if (density>=density_threshold):
        print('I know enough')
    else:
        print('I will ask you some questions')
        g2km.set_target_events_for_period(target, activity_type, gap_period)
        print("Set a goal for %s as a %s in state %s" % (target, activity_type, g2km.state.name))
        print('Desires', g2km.desires)

        while not g2km.state == ConvState.REACHED and not g2km.state == ConvState.GIVEUP:
            print('Intention', g2km._intention)
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
                object = g2km._intention["triple"]["object"]
                event_date = datetime.strptime(object['label'], '%Y-%m-%d %H:%M:%S')
                event = create_an_event(target, event_date, activity_type=activity_type)
                util.add_activities_to_ekg(brain, current_date, [event])

    ### For the FUTURE, we need to check if there are activities planned

    ### We first extract the list of dates that make up the FUTURE period
    future_period = pd.date_range(current_date.date(), FUTURE_PERIOD.date())
    print('The future is', future_period)
    # for date in future_period:
    #     print('Future date', date)
    #     for activity in future:
    #         if activity['time']==date:
    #             print('\tPlanned:', activity)
