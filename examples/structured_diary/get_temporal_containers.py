import cltl.g2kmore.thought_util as util
from datetime import datetime
from cltl.brain.long_term_memory import LongTermMemory
from cltl.commons.discrete import Certainty, Polarity, Sentiment, Emotion, GoEmotion

from random import choice
#from enum import Enum, auto
#
# certainties = [0, 0.2, 0.5, 0.7, 1]
# sentiments = [-1, -0.9, -0.8, -0.7, -0.6, -0.5, -0.4, -0.3, -0.2, -0.1, 0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]
# polarities = [0, 0.5, 1, 1, 1, 1]
#
# class GoNegEmotion(Enum):
#     FEAR = auto()
#     NERVOUSNESS = auto()
#     REMORSE = auto()
#     EMBARRASSMENT = auto()
#     DISAPPOINTMENT = auto()
#     SADNESS = auto()
#     GRIEF = auto()
#     DISGUST = auto()
#     ANGER = auto()
#     ANNOYANCE = auto()
#     DISAPPROVAL = auto()
#     REALIZATION = auto()
#     CONFUSION = auto()
#     @staticmethod
#     def random():
#         return choice(list(GoNegEmotion))
#
#
# class GoPosEmotion(Enum):
#     AMUSEMENT = auto()
#     EXCITEMENT = auto()
#     JOY = auto()
#     LOVE = auto()
#     DESIRE = auto()
#     OPTIMISM = auto()
#     CARING = auto()
#     PRIDE = auto()
#     ADMIRATION = auto()
#     GRATITUDE = auto()
#     RELIEF = auto()
#     APPROVAL = auto()
#     SURPRISE = auto()
#     CURIOSITY = auto()
#     CONFUSION = auto()
#     @staticmethod
#     def random():
#         return choice(list(GoPosEmotion))
#
# class GoEmotion(Enum):
#     NEUTRAL = auto()

def get_last_conversation_date (target:str, brain:LongTermMemory, current_date:datetime, fixed_previous_date:datetime):
    #### We get all utterances to get the date of the previous encounter
    query = util.get_all_utterances(target)
    brain_response = brain._submit_query(query)
    previous_conversation_date = None
    for result in brain_response:
        # print(result)
        year = ""
        month = ""
        day = ""
        if 'year' in result:
            year = result['year']['value']
        if 'month' in result:
            month = result['month']['value']
        if 'day' in result:
            day = result['day']['value']
        new_date = datetime(int(year) ,int(month), int(day))
        if previous_conversation_date:
            if new_date >previous_conversation_date:
                previous_conversation_date = new_date
        else:
            previous_conversation_date = new_date
    if not previous_conversation_date:
        previous_conversation_date = fixed_previous_date
    print('Our previous conservation was on', previous_conversation_date.strftime('%A'), previous_conversation_date)
    print("Today is", current_date.strftime('%A'), current_date)
    duration = current_date -previous_conversation_date
    print('What happened in the last', duration.days, 'days?')
    return previous_conversation_date

## This functions gets all activities from the eKG (brain) and creates a dict for important properties
## It returns 4 different lists as the temporal containers: history, gap, future and unknown time.
## the temporal containers are defined using the current_date and the date of the most recent conversation.
def get_temporal_containers (brain:LongTermMemory, current_date:datetime, recent_date:datetime, activity_type:str ="n2mu:icf", label:str=None):
    ##### We get all activities  and divide them into H, G, and F given now and the previous encounter
    history = []
    gap = []
    unknown = []
    future = []
    query = None
    if activity_type and label is None:
        # activity_type need to be full uri's prefixed with a namespace.
        # the standard namespace for activities is "n2mu", e.g. "n2my:icf"
        query = util.get_all_instances_query(activity_type)
    else:
        query = util.get_all_label_matches_query(label)
    print(query)
    brain_response = brain._submit_query(query)
    print('I found', len(brain_response), 'activities')
    #print(brain_response)
    for activity in brain_response:
        event_date = None
        event_location = None
        event_actors = []
        activity_id = activity["id"]["value"]
        if "label" in activity:
            activity_label= activity["label"]["value"]
        else:
            activity_label = label
        #### Get SEM relations
        query = util.get_sem_relation_query(activity_id)
        sem_response = brain._submit_query(query)
        for sem in sem_response:
            if 'actor_id' in sem:
                actor = sem['actor_id']['value']
                actor = actor[actor.rindex("/")+1:]
                if not actor in event_actors:
                    event_actors.append(actor)
            if 'place_id' in sem:
                event_location = sem['place_id']['value']
                event_location = event_location[event_location.rindex("/")+1:]
            if 'time_id' in sem:
                time = sem['time_id']['value']
                start=time.rindex('/')+1
                event_date = datetime.strptime(time[start:], '%Y-%m-%d_%H:%M:%S')
                ### To remove the time use the next code instead
                #end = time.rindex('_')
                #event_date = datetime.strptime(time[start:end], '%Y-%m-%d')

        #### Get perspectives
        emotion = GoEmotion.NEUTRAL
        certainty = Certainty.UNDERSPECIFIED
        sentiment = Sentiment.UNDERSPECIFIED
        polarity = Polarity.UNDERSPECIFIED
        query = util.get_perspective_query(activity_id)
        perspective_response = brain._submit_query(query)
        if perspective_response:
            for p in perspective_response:
                perspective = p['perspective_value']['value']
                attribute = perspective[perspective.rindex("/")+1:]
                value = perspective[perspective.rindex("#")+1:]
                if attribute.startswith("factuality"):
                    polarity = value
                elif attribute.startswith("sentiment"):
                    sentiment = Sentiment.from_str(value).value
                elif attribute.startswith("certainty"):
                    certainty = value
                # elif attribute.startswith("emotion"):
                #         emotion = GoEmotion.as_enum(value)

        ## Creating the data structure for each activity
        activity_result = {'id':activity_id, 'label':activity_label, "actors":event_actors, "location":event_location, "time": event_date,
                           #"perspective": len(event_perspectives)
                           'emotion': emotion,
                           'certainty': certainty,
                           'sentiment': sentiment,
                           'polarity': polarity
                           }

        ## Saving the activity in different temporal containers
        if not event_date:
            unknown.append(activity_result)
        elif event_date<recent_date:
            history.append(activity_result)
        elif event_date>current_date:
            future.append(activity_result)
        else:
            gap.append(activity_result)

    return history, gap, future, unknown