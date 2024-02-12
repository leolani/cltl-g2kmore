import cltl.g2kmore.thought_util as util
from datetime import datetime
from cltl.brain.long_term_memory import LongTermMemory
from random import choice
from enum import Enum, auto

certainties = [0, 0.2, 0.5, 0.7, 1]
#sentiments = [-10, -9, -8, -7, -6, -5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
sentiments = [-1, -0.9, -0.8, -0.7, -0.6, -0.5, -0.4, -0.3, -0.2, -0.1, 0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]
polarities = [0, 0.5, 1, 1, 1, 1]

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
        return choice(list(GoNegEmotion))


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
    CONFUSION = auto()
    @staticmethod
    def random():
        return choice(list(GoPosEmotion))

class GoEmotion(Enum):
    NEUTRAL = auto()

def get_last_conversation_date (target:str, brain:LongTermMemory, current_date:datetime):
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
    print(previous_conversation_date, previous_conversation_date.weekday(), previous_conversation_date.strftime('%A'))
    print("Today is", current_date.weekday(), current_date.strftime('%A'))
    duration = current_date -previous_conversation_date
    print('What happened in the last', duration.days, 'days?')
    return previous_conversation_date

## This functions gets all activities from the eKG (brain) and creates a dict for important properties
## It returns 4 different lists as the temporal containers: history, gap, future and unknown time.
## the temporal containers are defined using the current_date and the date of the most recent conversation.
def get_temporal_containers ( brain:LongTermMemory, current_date:datetime, recent_date:datetime):
    ##### We get all activities  and divide them into H, G, and F given now and the previous encounter
    history = []
    gap = []
    unknown = []
    future = []
    activity_tpe = "n2mu:icf"
    query = util.get_all_instances(activity_tpe)
    #print(query)
    brain_response = brain._submit_query(query)
    print('I found', len(brain_response), 'activities')
    #print(brain_response)
    for activity in brain_response:
        event_date = None
        event_location = None
        event_actors = []
        event_perspectives = [] #### To be fixed when properly stored in the eKG
        activity_id = activity["id"]["value"]
        activity_label= activity["label"]["value"]

        #### Get SEM relations
        query = util.get_sem_relations(activity_id)
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
                end = time.rindex('_')
                event_date = datetime.strptime(time[start:end], '%Y-%m-%d')

        #### Get perspectives
        ## Getting this from the brain does not work so we use random values as a hack
        ## HACK
        certainty = choice(certainties)
        sentiment = choice(sentiments)
        polarity = choice(polarities)
        emotion = GoEmotion.NEUTRAL
        if sentiment<-0.2:
            emotion = GoNegEmotion.random()
        elif sentiment>0.2:
            emotion = GoPosEmotion.random()
        ## END OF HACK

        ## Get the perspectives from the brain when it works
        # query = util.get_perspectives(activity_id)
        # #print('perspective query', query)
        # perspective_response = brain._submit_query(query)
        # for p in perspective_response:
        #     perspective = p['perspective_value']['value']
        #     perspective = perspective[perspective.rindex("#")+1:]
        #     if not perspective=="UNDERSPECIFIED":
        #         print(p)
        #         event_perspectives.append(perspective)

        ## Simulating asking questions, this needs to be done through the interaction
        # if not event_actors:
        #     print("Tell me more about", activity_label)
        # if not event_date:
        #     print("Tell me when was", activity_label)
        # if not event_location:
        #     print("Tell me where was", activity_label)
        # if not event_perspectives:
        #     print("Tell me how was", activity_label)

        ## Creatng the data structure for each activity
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