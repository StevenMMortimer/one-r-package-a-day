# script.py
from os import environ
from os.path import join, dirname
from dotenv import load_dotenv
from re import sub
import pandas
from TwitterAPI import TwitterAPI, TwitterPager

# Create .env file path.
dotenv_path = join(dirname(__file__), '.env')

# Load file from the path.
load_dotenv(dotenv_path)

if __name__ == "__main__":
    #twitter = TwitterAPI()
    #twitter.tweet("Hello world!")

    api = TwitterAPI(consumer_key=environ['TWITTER_CONSUMER_KEY'],
                     consumer_secret=environ['TWITTER_CONSUMER_SECRET'],
                     access_token_key=environ['TWITTER_ACCESS_TOKEN'],
                     access_token_secret=environ['TWITTER_ACCESS_TOKEN_SECRET'])

    SCREEN_NAME = 'RLangPackage'
    pager = TwitterPager(api,
                         'statuses/user_timeline',
                         {'screen_name': SCREEN_NAME, 'count': 100})

    previous_pks = []
    for item in pager.get_iterator(wait=3.5):
        if 'text' in item:
            this_pkg = sub("^(\w+) - (.*)", "\\1", item['text'])
            previous_pks.append(this_pkg)

    prev_df = pandas.DataFrame({'name': previous_pks})
    prev_df.set_index('name')

    url = "https://raw.githubusercontent.com/StevenMMortimer/one-r-package-a-day/master/r-package-star-download-data.csv"
    all_df = pandas.read_csv(url)
    all_df.set_index('name')

    all_df = pandas.merge(all_df, prev_df, how='outer', indicator=True)
    all_df = all_df[all_df['_merge'] == 'left_only']

    # focus on packages in middle ground of downloads and stars
    filtered_df = all_df[all_df['stars'].notnull()]
    filtered_df = filtered_df[filtered_df['stars'].between(10,1000)]
    filtered_df = filtered_df[filtered_df['downloads'].notnull()]
    filtered_df = filtered_df[filtered_df['downloads'].between(5000, 1000000)]

    selected_pkg = filtered_df.sample(1)
    name_len = len(selected_pkg.iloc[0]['name'])
    desc_len = len(selected_pkg.iloc[0]['description'])
    prepped_name = selected_pkg.iloc[0]['name']
    if desc_len <= (280-4-23-name_len):
        prepped_desc = selected_pkg.iloc[0]['description'][0:(280-4-23-name_len)]
    else:
        prepped_desc = selected_pkg.iloc[0]['description'][0:(280-7-23-name_len)] + "..."

    TWEET_TEXT = prepped_name + " - " + prepped_desc + " " + selected_pkg.iloc[0]['github_url']
    print(prepped_name + " - " + prepped_desc + " " + selected_pkg.iloc[0]['github_url'])

    #TWEET_TEXT = "Hello World!"
    r = api.request('statuses/update', {'status': TWEET_TEXT})
    print('SUCCESS' if r.status_code == 200 else 'PROBLEM: ' + r.text)