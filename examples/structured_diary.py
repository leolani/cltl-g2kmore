from datetime import datetime, timedelta
from generate_events import create_a_life
import logging
import os
from pathlib import Path
import seaborn as sns
import enum
import json
import pandas as pd
import matplotlib.pyplot as plt
import get_temporal_containers as query
from cltl.brain.long_term_memory import LongTermMemory
from cltl.reply_generation.lenka_replier import LenkaReplier


import cltl.g2kmore.thought_util as util
from cltl.g2kmore.brain_g2kmore import BrainGetToKnowMore, ConvState
logger = logging.getLogger(__name__)

n2mu = "http://cltl.nl/leolani/n2mu/"

class Factuality(enum.Enum):
    REALIS = 1 # polarity: 1.0
    IRREALIS = 2 # polarity: 0.5
    DENIED = 3 # polarity: 0.0

def get_temporal_container (activities, curent_date):
    earliest_day = current_date
    latest_day = current_date
    for activity in activities:
        if activity['time']<earliest_day:
            earliest_day = activity['time']
        elif activity['time']>latest_day:
            latest_day=activity['time']
    period = pd.date_range(earliest_day.date(), latest_day.date())
    print(period)
    activity_in_period = []
    for date in period:
        activity_on_date = {'id':"", 'label':"None",  "time": date, "perspective": 0}

        for activity in activities:
            if activity['time']==date:
                activity_on_date = activity
        activity_in_period.append(activity_on_date)
    return earliest_day, latest_day, period, activity_in_period

def add_activity_to_ekg(brain: LongTermMemory, current_date, activities):
    #### We need to create a context for adding data to the eKG
    context = util.make_context()
    response = brain.capsule_context(context)
    print("response pushing context", response)
    chat = str(current_date.timestamp())
    turn = "_1"

    for activity in activities:
        print(activity)
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
            #emotion = GoEmotion.DISAPPOINTMENT  ### we want to replace the numeric value with a categorical value
            #factuality = Factuality.REALIS  ### we want to replace the numeric value with a categorical value
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

    replier = LenkaReplier()
    haydo = BrainGetToKnowMore(brain, max_attempts=10, max_intention_attempts=3)

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
    print(recent_date)
    history, gap, future, unknown = query.get_temporal_containers(brain, current_date, recent_date)


    print('History before', recent_date, len(history), " activities")
    print("\t", history)
    print('Gap between', recent_date, " and ", current_date, len(gap), " activities")
    print("\t", gap)
    print('Future after', current_date, len(future), " activities")
    print("\t", future)
    print('Unknown date', len(unknown), ' activities')
    print("\t", unknown)

    story_of_life = history+gap+future
    earliest, latest, period, activity_in_period  = get_temporal_container(story_of_life, curent_date=current_date)
    df = pd.DataFrame(activity_in_period, index=period)

 #   ax = sns.catplot(x='time', y='sentiment', kind='swarm', hue='label', data=df)
 #   ax = sns.swarmplot(x='time', y='sentiment', hue='label', data=df)
    #ax = sns.lineplot(x='time', y='sentiment', hue='label', data=df) #hue='label',
    sns.set_style("darkgrid", {"grid.color": ".6", "grid.linestyle": ":"})

    ax = sns.scatterplot(x='time', y='sentiment', hue='label', data=df,  style='label', palette="deep", sizes=(20, 200), legend="full")

    # Add labels at the peak points
    #for category in df['label'].unique():
    #    max_point = df[df['label'] == category]['label'].max()
    #    max_date = df[(df['label'] == category) & (df['perspective'] == max_point)]['time'].values[0]
    #     if not category=="None":
    #         ax.text(df['time'], max_point, f'{max_point}', ha='left', va='bottom',
    #                color=ax.get_lines()[df['label'].unique().tolist().index(category)].get_c())
    for index in df.index:
        x = df['time'][index]
        y = df['sentiment'][index]
        category = df['label'][index]
        actors = df['actors'][index]
        polarity = df['polarity'][index]
        emotion = df['emotion'][index]
        realis = "ir"
        if polarity<0.5:
            realis="de"
        elif polarity>0.5:
            realis="re"
        if not category=="None":
            ax.text(x, y, s=" "+str(category)+str(actors)+"\n   "+str(emotion.name)+"_"+realis, horizontalalignment='left', size='small', color='black', verticalalignment='bottom', linespacing=2)


    ax.tick_params(axis='x', rotation=70)
    # Show the plot
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0)
    plt.show()
    path = target+".png"
    plt.savefig(path, dpi=300, transparent=True)

