import logging
import time
from datetime import datetime
from urllib import parse

import editdistance
import os
import re
import requests
from collections import defaultdict
from geopy import distance
from twitter import TwitterError

from src.clients.apple_client import AppleClient
from src.clients.fb_client import FbClient
from src.clients.twitter_client import TwitterClient

if os.path.isfile('./src/credentials.py'):
    from src.credentials import POKEMON_FEEDS, IPHONE_NAME
else:
    POKEMON_FEEDS = ['TWITTER_SCREEN_NAME']
    IPHONE_NAME = 'DEVICE_NAME'

SLEEP_SECS = 5 * 60
MAX_MILES_DISTANCE = 10.0
MAX_SIMILAR_TWEET = 10

log = logging.getLogger('src.script')


def get_pokemon_tweets(twitter_client, since_pokemon_tweet, max_pokemon_tweet):
    def new_enough(tweet, now):
        tweet_time = datetime.fromtimestamp(tweet.created_at_in_seconds)
        return (now - tweet_time).total_seconds() < SLEEP_SECS

    all_tweets = []
    for screen_name in POKEMON_FEEDS:
        while True:
            log.warning('Fetching tweets for screen_name: {} with max_id: {} and since_id: {}'.format(
                screen_name, max_pokemon_tweet[screen_name], since_pokemon_tweet[screen_name]))
            try:
                tweets = twitter_client.GetUserTimeline(screen_name=screen_name,
                                                        max_id=max_pokemon_tweet[screen_name],
                                                        since_id=since_pokemon_tweet[screen_name],
                                                        count=200)
            except TwitterError as e:
                log.warning('Failed to fetch tweets for screen_name: {} with max_id: {} and since_id: {}'.format(
                    screen_name, max_pokemon_tweet[screen_name], since_pokemon_tweet[screen_name]), exc_info=True)
                tweets = []

            if not tweets:
                log.warning('No more tweets for screen_name: {}'.format(screen_name))
                break
            max_pokemon_tweet[screen_name] = min([tweet.id for tweet in tweets])
            since_pokemon_tweet[screen_name] = max([tweet.id for tweet in tweets])

            log.warning('Successfully fetched {} tweets'.format(len(tweets)))
            now = datetime.now()
            tweets = [tweet for tweet in tweets if new_enough(tweet, now)]
            if not tweets:
                log.warning('No more recent tweets for screen_name: {}'.format(screen_name))
                break
            else:
                log.warning('Finalized tweet filter by recent time. Got {} for screen_name: {}'.format(
                    len(tweets), screen_name))
            all_tweets.extend(tweets)

    return all_tweets


def extract_location(location):
    return location['latitude'], location['longitude']


def filter_tweets_by_location(tweets, location):
    def fetch_pokemon_location_from_tweet(poke_tweet):
        urls = re.findall('(?P<url>https?://[^\s]+)', poke_tweet.text)

        for url in urls:
            resp = requests.head(url=url)
            yield tuple(parse.parse_qs(parse.urlparse(resp.headers['location']).query)['q'])

    filtered_tweets = set()
    for tweet in tweets:
        for pokemon_location in fetch_pokemon_location_from_tweet(tweet):
            if distance.distance(location, pokemon_location).miles < MAX_MILES_DISTANCE:
                filtered_tweets.add(tweet.text)

    return filtered_tweets


def merge_same_pokemon(tweets):
    filtered_tweets = []
    for tested_tweet in tweets:
        if not any([editdistance.eval(tested_tweet, tweet) <= MAX_SIMILAR_TWEET
                    for tweet in tweets if tweet != tested_tweet]):
            filtered_tweets.append(tested_tweet)

    return filtered_tweets


def main():
    last_pokemon_tweet = defaultdict(int)

    log.warning('Logging in to Facebook Messenger!')
    fb_client = FbClient()
    log.warning('----------------------------------------------------------------------------')

    log.warning('Logging in to Apple iCloud!')
    apple_client = AppleClient(fb_client=fb_client)
    log.warning('----------------------------------------------------------------------------')

    log.warning('Logging in to Twitter!')
    twitter_client = TwitterClient()
    log.warning('----------------------------------------------------------------------------')

    while True:
        log.warning('Another iteration!')
        log.warning('----------------------------------------------------------------------------')

        tweets = get_pokemon_tweets(twitter_client, last_pokemon_tweet, defaultdict(int))
        log.warning('Got {} tweets for this iteration!'.format(len(tweets)))

        if tweets:
            tweets = filter_tweets_by_location(tweets, extract_location(apple_client.get_location(IPHONE_NAME)))
            log.warning('Got {} location (close to you) filtered tweets for this iteration!'.format(len(tweets)))

        if tweets:
            tweets = merge_same_pokemon(tweets)
            log.warning('Got {} merged (same pokemon) filtered tweets for this iteration!'.format(len(tweets)))

        if tweets:
            for tweet in tweets:
                fb_client.send_message_to_poke_thread(tweet)
            log.warning('Sent Facebook notifications (to your group) for all nearby pokemon!')

        time.sleep(SLEEP_SECS)
        log.warning('')


if __name__ == '__main__':
    main()
