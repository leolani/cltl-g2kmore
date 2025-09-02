import random
from typing import Hashable

import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime
import logging
import os
import pandas as pd
from pathlib import Path
import get_temporal_containers as query
from cltl.brain.long_term_memory import LongTermMemory
import cltl.g2kmore.thought_util as util

logger = logging.getLogger(__name__)

def get_activity_in_period(activities:[], current_date: datetime):
    earliest_day = current_date
    latest_day = current_date
    for activity in activities:
        if activity['time']<earliest_day:
            earliest_day = activity['time']
        elif activity['time']>latest_day:
            latest_day=activity['time']
    dates = pd.date_range(earliest_day.date(), latest_day.date())
    period_dict = {}
    for date in dates:
        date_activity = []
        for activity in activities:
            if activity['time'].date()==date.date():
                date_activity.append(activity)
        period_dict[date]=date_activity
    activity_in_period = []
    period = []
    for date in period_dict:
        date_activities = period_dict.get(date)
        for activity in date_activities:
            period.append(activity['time'])
            activity_in_period.append(activity)
    return earliest_day, latest_day, period, activity_in_period

def create_timeline_image(name:str, story_of_life:[], target:str,  current_date: datetime):
    earliest, latest, period, activity_in_period = get_activity_in_period(story_of_life, current_date=current_date)
    df = pd.DataFrame(activity_in_period, index=period)
    plt.rcParams['figure.figsize'] = [2.0 * len(activity_in_period), 10]

    sns.set_style("whitegrid", {"grid.color": ".8", "grid.linestyle": ":", 'axes.grid': True})
    sns.set_context("talk", font_scale=1.0)
    ### other themes: paper, talk, poster, notebook (default)

    #print(df.head())
 #   ax = sns.scatterplot(x='time', y='sentiment', hue='label', data=df, size="certainty", style='label', palette="deep", sizes=(20, 200), legend="full")
    ax = sns.lineplot(x='time', y='sentiment', hue='label', data=df, size="certainty", palette="pastel", legend="brief", marker="o")
    # palette = "pastel, flare/bright/deep/muted/colorblind/dark"

    for index, row in df.iterrows():
        x = row['time']
        y = row['sentiment']
        category = row['label']
        actors = row['actors']
        polarity = row['polarity']
        emotion = row['emotion']

        ax.text(x, y,
             #   s=" " + str(category) + str(actors) + "\n   " + str(emotion.name).lower() + "_" + polarity,
                s=" " + str(category) + str(actors) + "\n" ,
                rotation=50,
                horizontalalignment='left', size='small', color='black', verticalalignment='bottom',
                linespacing=1.5)

    ax.tick_params(axis='x', rotation=70)
    # Show the plot
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0)
    path = name+ "_"+target + ".png"
    # plt.savefig(path, dpi=300, transparent=True)
    plt.savefig(path)
    plt.show()

def create_bio_image(name:str, story_of_life:[], target:str,  current_date: datetime):
    earliest, latest, period, activity_in_period = get_activity_in_period(story_of_life, current_date=current_date)
    df = pd.DataFrame(activity_in_period, index=period)
    plt.rcParams['figure.figsize'] = [0.5 * len(activity_in_period), 10]

    sns.set_style("whitegrid", {"grid.color": ".8", "grid.linestyle": ":", 'axes.grid': True})
    sns.set_context("talk", font_scale=0.5)
    ax = sns.lineplot(x='time', y='sentiment', hue='label', data=df, size="certainty",  palette="pastel", legend="brief", marker="o")
 #   ax = sns.lineplot(x='time', y='sentiment', hue='label', data=df, palette="pastel")
    # palette = "pastel, flare/bright/deep/muted/colorblind/dark"
    cnt = 0
    for index, row in df.iterrows():
        cnt +=1
        x = row['time']
        y = row['sentiment']
        activity = row['activity']+":\n"
        agent_list = row['agents']
        patient_list = row['patients']
        polarity = row['polarity']
        emotion = row['emotion']
        agents = "    "
        patients = ""
        for i, actor in enumerate(agent_list):
            if i>0 and i%5==0:
                agents+="\n"
            agents += actor+";"
        if len(patient_list)>0:
            patients = "    "
        for i, patient in enumerate(patient_list):
            if i>0: # and i%5==0:
                patients+="\n    "
            patients += patient
        # alternate angles: +45°, -45°
        angle = 60 #  if cnt % 2 == 0 else 60
        # offset vertically to prevent overlap with marker
        y_offset = 3 if cnt % 2 == 0 else -3
        ax.text(x, y,
                s=" " + str(activity) + patients + "\n" ,
                rotation=angle,
                horizontalalignment='left', size='small', color='black', verticalalignment='bottom',
                linespacing=1.5)

    ax.tick_params(axis='x') #, rotation=70
    # Show the plot
    plt.legend(bbox_to_anchor=(1.01, 1), loc='upper left', borderaxespad=0)
    path = name+ "_"+target + ".png"
    plt.savefig(path, dpi=300) #,  transparent=True
   # plt.savefig(path)
    plt.show()




if __name__ == "__main__":

    what = "bio"

    event_type="activity"
    target = "Abdullah"
    target = "Jan"
   # target = "Maria"
    activity_type = "n2mu:activity"
    activity_label = "dinner"
    current_date = datetime.today()
    #### We can simulate another day as now!
    current_date = datetime(2015, 7, 1)
    PREVIOUS_DATE = datetime(2010,2, 1)
    FUTURE_PERIOD = datetime(2024, 2, 10)


    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    log_path = "log_path"
    if not os.path.exists(log_path):
        dir = os.mkdir(log_path)
    brain = LongTermMemory(address="http://localhost:7200/repositories/diabetes",
                           log_dir=Path(log_path), clear_all=False)

    if what=="bio":
        story_of_life = query.get_temporal_container_for_agent(brain, agent=target, activity_type=activity_type)
        print('Found:', len(story_of_life), "activities for", target)
        if len(story_of_life)>0:
            create_bio_image(activity_type, story_of_life, target, current_date)
    else:
            recent_date = query.get_last_conversation_date(target, brain, current_date, PREVIOUS_DATE)
            #history, gap, future, unknown = query.get_temporal_containers(brain, current_date, recent_date)

            history, gap, future, unknown = query.get_temporal_containers(brain, current_date, PREVIOUS_DATE, activity_type="n2mu:activity", label=None)

            print('History before', recent_date, len(history), " activities")
            print("\t", history)
            print('Gap between', recent_date, " and ", current_date, len(gap), " activities")
            print("\t", gap)
            print('Future after', current_date, len(future), " activities")
            print("\t", future)
            print('Unknown date', len(unknown), ' activities')
            print("\t", unknown)

            story_of_life = history + gap + future
            if len(story_of_life)>0:
                create_timeline_image(activity_type, story_of_life, target, current_date)

            history, gap, future, unknown = query.get_temporal_containers(brain, current_date, PREVIOUS_DATE, activity_type=None, label = activity_label)

            print('History before', recent_date, len(history), " activities")
            print("\t", history)
            print('Gap between', recent_date, " and ", current_date, len(gap), " activities")
            print("\t", gap)
            print('Future after', current_date, len(future), " activities")
            print("\t", future)
            print('Unknown date', len(unknown), ' activities')
            print("\t", unknown)

            story_of_life = history + gap + future
            if len(story_of_life) > 0:
                create_timeline_image(activity_label, story_of_life, target, current_date)

