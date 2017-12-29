import os

from twitter import Api

if os.path.isfile('./src/credentials.py'):
    from src.credentials import TWITTER_API_CONSUMER_KEY, TWITTER_API_CONSUMER_SECRET, TWITTER_API_ACCESS_TOKEN_KEY, \
        TWITTER_API_ACCESS_TOKEN_SECRET
else:
    TWITTER_API_CONSUMER_KEY = 'REPLACE_KEY'
    TWITTER_API_CONSUMER_SECRET = 'REPLACE_SECRET'
    TWITTER_API_ACCESS_TOKEN_KEY = 'REPLACE_ACCESS_KEY'
    TWITTER_API_ACCESS_TOKEN_SECRET = 'REPLACE_ACCESS_SECRET'


class TwitterClient(Api):
    def __init__(self, **kwargs):
        kwargs['consumer_key'] = TWITTER_API_CONSUMER_KEY
        kwargs['consumer_secret'] = TWITTER_API_CONSUMER_SECRET
        kwargs['access_token_key'] = TWITTER_API_ACCESS_TOKEN_KEY
        kwargs['access_token_secret'] = TWITTER_API_ACCESS_TOKEN_SECRET
        super(TwitterClient, self).__init__(**kwargs)
