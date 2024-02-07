import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime


def get_temporal_container(activities:[], current_date: datetime):
    earliest_day = current_date
    latest_day = current_date
    for activity in activities:
        if activity['time']<earliest_day:
            earliest_day = activity['time']
        elif activity['time']>latest_day:
            latest_day=activity['time']
    period = pd.date_range(earliest_day.date(), latest_day.date())
    activity_in_period = []
    for date in period:
        activity_on_date = {'id':"", 'label':"None",  "time": date, "perspective": 0}

        for activity in activities:
            if activity['time']==date:
                activity_on_date = activity
        activity_in_period.append(activity_on_date)
    return earliest_day, latest_day, period, activity_in_period

def create_timeline_image(story_of_life:[], target:str,  current_date: datetime):
    earliest, latest, period, activity_in_period = get_temporal_container(story_of_life, current_date=current_date)
    df = pd.DataFrame(activity_in_period, index=period)

    sns.set_style("darkgrid", {"grid.color": ".6", "grid.linestyle": ":"})

    ax = sns.scatterplot(x='time', y='sentiment', hue='label', data=df, size="certainty", style='label', palette="deep",
                         sizes=(20, 200), legend="full")
    for index in df.index:
        x = df['time'][index]
        y = df['sentiment'][index]
        category = df['label'][index]
        actors = df['actors'][index]
        polarity = df['polarity'][index]
        emotion = df['emotion'][index]
        realis = "ir"
        if polarity < 0.5:
            realis = "de"
        elif polarity > 0.5:
            realis = "re"
        if not category == "None":
            ax.text(x, y, s=" " + str(category) + str(actors) + "\n   " + str(emotion.name).lower() + "_" + realis,
                    horizontalalignment='left', size='xx-small', color='black', verticalalignment='bottom',
                    linespacing=1)

    ax.tick_params(axis='x', rotation=70)
    # Show the plot
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0)
    path = target + ".png"
    # plt.savefig(path, dpi=300, transparent=True)
    plt.savefig(path)
    plt.show()