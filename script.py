# script.py
from os import environ
from os.path import join, dirname
from dotenv import load_dotenv
from re import sub, findall
import pandas
from TwitterAPI import TwitterAPI, TwitterPager

# create .env file path
dotenv_path = join(dirname(__file__), '.env')

# load file from the path
load_dotenv(dotenv_path)

if __name__ == "__main__":

    # connect to api
    api = TwitterAPI(consumer_key=environ['TWITTER_CONSUMER_KEY'],
                     consumer_secret=environ['TWITTER_CONSUMER_SECRET'],
                     access_token_key=environ['TWITTER_ACCESS_TOKEN'],
                     access_token_secret=environ['TWITTER_ACCESS_TOKEN_SECRET'])

    # scrape all prior tweets to check which packages I've already tweeted about
    SCREEN_NAME = 'RLangPackage'
    pager = TwitterPager(api,
                         'statuses/user_timeline',
                         {'screen_name': SCREEN_NAME, 'count': 100})

    # parse out the package name that occurs before the hyphen at the beginning
    previous_pks = []
    for item in pager.get_iterator(wait=3.5):
        if 'text' in item:
            this_pkg = sub("^([A-Za-z0-9.]+) - (.*)", "\\1", item['text'])
            previous_pks.append(this_pkg)

    # add packrat, it wasn't formatted correctly when it tweeted
    previous_pks.append('packrat')

    # convert the package names to a dataframe
    prev_df = pandas.DataFrame({'name': previous_pks})
    prev_df.set_index('name')

    # load the data I've compiled on R packages
    url = "https://raw.githubusercontent.com/StevenMMortimer/one-r-package-a-day/master/r-package-star-download-data.csv"
    all_df = pandas.read_csv(url)
    all_df.set_index('name')

    # do an "anti join" to throw away previously tweeted rows
    all_df = pandas.merge(all_df, prev_df, how='outer', indicator=True)
    all_df = all_df[all_df['_merge'] == 'left_only']

    # focus on packages in middle ground of downloads and stars
    filtered_df = all_df[all_df['stars'].notnull()]
    filtered_df = filtered_df[filtered_df['stars'].between(10,1000)]
    filtered_df = filtered_df[filtered_df['downloads'].notnull()]
    filtered_df = filtered_df[filtered_df['downloads'].between(5000, 1000000)]

    # randomly select one of the remaining rows
    selected_pkg = filtered_df.sample(1)

    # pull out the name and description to see if we need to truncate because of Twitters 280 character limit
    prepped_name = selected_pkg.iloc[0]['name']
    prepped_desc = sub('\s+', ' ', selected_pkg.iloc[0]['description'])
    # determine how many urls are in the description since Twitter shortens or expands all URLs to 23 chars
    urls_count = len(findall("https|http|\bwww|<www", prepped_desc))

    name_len = len(prepped_name)
    desc_len = len(prepped_desc)

    # 280 tweet char max
    # then minus 3 for " - "
    # then minus 9 for the " #rstats " hashtag
    # then minus the number of urls plus one github url times 23 because all links are counted as 23 chars
    if desc_len <= (280-3-((urls_count+1)*23)-9-name_len):
        prepped_desc = prepped_desc[0:desc_len]
    else:
        # minus 6 instead of 3 for the added "..."
        prepped_desc = prepped_desc[0:(280-6-((urls_count+1)*23)-9-name_len)] + "..."

    # cobble together the tweet text
    TWEET_TEXT = prepped_name + " - " + prepped_desc + " #rstats " + selected_pkg.iloc[0]['github_url']
    print(TWEET_TEXT)

    # tweet it out to the world!
    r = api.request('statuses/update', {'status': TWEET_TEXT})
    print('SUCCESS' if r.status_code == 200 else 'PROBLEM: ' + r.text)