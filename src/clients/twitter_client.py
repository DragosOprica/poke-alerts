import logging
from datetime import datetime, timezone

import os
from collections import defaultdict
from twitter import Api
from twitter import TwitterError

if os.path.isfile('./src/credentials.py'):
    from src.credentials import TWITTER_API_CONSUMER_KEY, TWITTER_API_CONSUMER_SECRET, TWITTER_API_ACCESS_TOKEN_KEY, \
        TWITTER_API_ACCESS_TOKEN_SECRET, TWITTER_POKEMON_FEEDS
else:
    TWITTER_API_CONSUMER_KEY = 'REPLACE_KEY'
    TWITTER_API_CONSUMER_SECRET = 'REPLACE_SECRET'
    TWITTER_API_ACCESS_TOKEN_KEY = 'REPLACE_ACCESS_KEY'
    TWITTER_API_ACCESS_TOKEN_SECRET = 'REPLACE_ACCESS_SECRET'
    TWITTER_POKEMON_FEEDS = ['TWITTER_SCREEN_NAME']

log = logging.getLogger('client.twitter_client')

SLEEP_SECS = 60
MAX_TWEETS_PER_REQUEST = 200


class TwitterClient(Api):
    def __init__(self, **kwargs):
        kwargs['consumer_key'] = TWITTER_API_CONSUMER_KEY
        kwargs['consumer_secret'] = TWITTER_API_CONSUMER_SECRET
        kwargs['access_token_key'] = TWITTER_API_ACCESS_TOKEN_KEY
        kwargs['access_token_secret'] = TWITTER_API_ACCESS_TOKEN_SECRET
        super(TwitterClient, self).__init__(**kwargs)
        self.feeds = TWITTER_POKEMON_FEEDS
        self.ttl = kwargs.get('ttl', SLEEP_SECS)
        self.since_pokemon_tweet = defaultdict(int)

    def _new_enough(self, tweet, now):
        tweet_time = datetime.fromtimestamp(tweet.created_at_in_seconds, tz=timezone.utc)
        return (now - tweet_time).total_seconds() < self.ttl

    def get_pokemon_tweets(self):
        max_pokemon_tweet = defaultdict(int)

        all_tweets = []
        for screen_name in self.feeds:
            while True:
                log.warning('Fetching tweets for screen_name: {} with max_id: {} and since_id: {}'.format(
                    screen_name, max_pokemon_tweet[screen_name], self.since_pokemon_tweet[screen_name]))
                try:
                    tweets = self.GetUserTimeline(screen_name=screen_name,
                                                  max_id=max_pokemon_tweet[screen_name],
                                                  since_id=self.since_pokemon_tweet[screen_name],
                                                  count=MAX_TWEETS_PER_REQUEST)
                except TwitterError as e:
                    log.warning('Failed to fetch tweets for screen_name: '
                                '{} with max_id: {} and since_id: {}'.format(screen_name,
                                                                             max_pokemon_tweet[screen_name],
                                                                             self.since_pokemon_tweet[screen_name]),
                                exc_info=True)
                    tweets = []

                if not tweets:
                    log.warning('No more tweets for screen_name: {}'.format(screen_name))
                    break

                max_pokemon_tweet[screen_name] = min([tweet.id for tweet in tweets])
                self.since_pokemon_tweet[screen_name] = max([tweet.id for tweet in tweets])

                log.warning('Successfully fetched {} tweets'.format(len(tweets)))
                now = datetime.now(tz=timezone.utc)
                tweets = [tweet for tweet in tweets if self._new_enough(tweet, now)]
                if not tweets:
                    log.warning('No more recent tweets for screen_name: {}'.format(screen_name))
                else:
                    log.warning('Finalized tweet filter by recent time. Got {} for screen_name: {}'.format(
                        len(tweets), screen_name))
                all_tweets.extend(tweets)

                if len(tweets) != MAX_TWEETS_PER_REQUEST:
                    break

        return all_tweets
