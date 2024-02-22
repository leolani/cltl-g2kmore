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

def create_timeline_image(story_of_life:[], target:str,  current_date: datetime):
    earliest, latest, period, activity_in_period = get_activity_in_period(story_of_life, current_date=current_date)
    df = pd.DataFrame(activity_in_period, index=period)
    sns.set_style("darkgrid", {"grid.color": ".6", "grid.linestyle": ":"})
    #print(df.head())
 #   ax = sns.scatterplot(x='time', y='sentiment', hue='label', data=df, size="certainty", style='label', palette="deep", sizes=(20, 200), legend="full")
    ax = sns.lineplot(x='time', y='sentiment', hue='label', data=df, size="certainty", palette="deep", legend="full")

    for index, row in df.iterrows():
        x = row['time']
        y = row['sentiment']
        category = row['label']
        actors = row['actors']
        polarity = row['polarity']
        emotion = row['emotion']

        ax.text(x, y,
                s=" " + str(category) + str(actors) + "\n   " + str(emotion.name).lower() + "_" + polarity,
                horizontalalignment='left', size='small', color='black', verticalalignment='bottom',
                linespacing=1)

    ax.tick_params(axis='x', rotation=70)
    # Show the plot
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0)
    path = target + ".png"
    # plt.savefig(path, dpi=300, transparent=True)
    plt.savefig(path)
    plt.show()



if __name__ == "__main__":

    event_type="icf"
    target = "carl"
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

    # activity_tpe = "n2mu:icf"
    # activity_query = util.get_all_instances_query(activity_tpe)
    # story_of_life = brain._submit_query(activity_query)

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

    story_of_life = history + gap + future
    if len(story_of_life)>0:
        create_timeline_image(story_of_life, target, current_date)

