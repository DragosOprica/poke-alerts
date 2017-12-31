import logging
import re
import time
from urllib import parse

import os
import requests
from geopy import distance

from src.clients.apple_client import AppleClient
from src.clients.discord_client import DiscordClient
from src.clients.fb_client import FbClient
from src.clients.twitter_client import TwitterClient

if os.path.isfile('./src/credentials.py'):
    from src.credentials import POKEMON_LIST
else:
    POKEMON_LIST = ['POKEMON_NAME']

SLEEP_SECS = 60
MAX_MILES_DISTANCE = 0.5
MIN_DISTANCE_FEET = 5

log = logging.getLogger('src.script')


def filter_tweets_by_location(tweets, location):
    def fetch_pokemon_location(poke_tweet):
        urls = re.findall('(?P<url>https?://[^\s]+)', poke_tweet.text)

        for url in urls:
            resp = requests.head(url=url)
            try:
                return parse.parse_qs(parse.urlparse(resp.headers['location']).query)['q'][0]
            except Exception as e:
                log.warning('Failed to parse location for url {}'.format(url), exc_info=True)
        return ['0, 0']

    filtered_tweets = set()
    for tweet in tweets:
        pokemon_location = fetch_pokemon_location(tweet)
        if distance.distance(location, pokemon_location).miles < MAX_MILES_DISTANCE:
            filtered_tweets.add((pokemon_location, tweet.text))

    return filtered_tweets


def filter_discord_messages_by_location(messages, location):
    def fetch_pokemon_location(message):
        try:
            return parse.parse_qs(parse.urlparse(message['embeds'][0]['url']).query)['q'][0]
        except Exception as e:
            log.warning('Failed to parse location for message {}'.format(message), exc_info=True)
            return ['0, 0']

    filtered_messages = set()
    for message in messages:
        pokemon_location = fetch_pokemon_location(message)
        if distance.distance(location, pokemon_location).miles < MAX_MILES_DISTANCE:
            try:
                filtered_messages.add((pokemon_location,
                                       message['embeds'][0]['title'] + '\n' + message['embeds'][0]['description']))
            except (KeyError, TypeError) as e:
                log.warning('Failed to parse message text for message {}'.format(message), exc_info=True)

    return filtered_messages


def merge_same_pokemon(pokemons):
    def same_poke(loc_a, loc_b, text_a, text_b):
        if distance.distance(loc_a, loc_b).feet > MIN_DISTANCE_FEET:
            return False

        candidate_a = [pokemon for pokemon in POKEMON_LIST if pokemon.lower() in text_a.lower()][0]
        candidate_b = [pokemon for pokemon in POKEMON_LIST if pokemon.lower() in text_b.lower()][0]
        if candidate_a != candidate_b:
            return False

        return True

    filtered_pokemons = []
    for current_location, current_text in pokemons:
        if not any([same_poke(current_location, filtered_location, current_text, filtered_text)
                    for filtered_location, filtered_text in filtered_pokemons]):
            filtered_pokemons.append((current_location, current_text))

    return [text for _, text in filtered_pokemons]


def main():
    log.warning('Logging in to Facebook Messenger!')
    fb_client = FbClient()
    log.warning('----------------------------------------------------------------------------')

    log.warning('Logging in to Apple iCloud!')
    apple_client = AppleClient(fb_client=fb_client)
    log.warning('----------------------------------------------------------------------------')

    log.warning('Logging in to Twitter!')
    twitter_client = TwitterClient()
    log.warning('----------------------------------------------------------------------------')

    log.warning('Logging in to Discord!')
    discord_client = DiscordClient()
    log.warning('----------------------------------------------------------------------------')

    while True:
        log.warning('Another iteration!')
        log.warning('----------------------------------------------------------------------------')
        tweets = twitter_client.get_pokemon_tweets()
        log.warning('Got {} tweets for this iteration!'.format(len(tweets)))
        log.warning('----------------------------------------------------------------------------')
        messages = discord_client.get_pokemon_messages()
        log.warning('Got {} discord messages for this iteration!'.format(len(messages)))
        log.warning('----------------------------------------------------------------------------')
        location = apple_client.get_location()

        pokemons = []
        if tweets:
            local_pokemon = filter_tweets_by_location(tweets, location)
            pokemons.extend(local_pokemon)
            log.warning('Got {} location filtered tweets for this iteration!'.format(len(local_pokemon)))
        if messages:
            local_pokemon = filter_discord_messages_by_location(messages, location)
            pokemons.extend(local_pokemon)
            log.warning('Got {} location filtered messages for this iteration!'.format(len(local_pokemon)))

        if pokemons:
            pokemons = merge_same_pokemon(pokemons)
            log.warning('Got {} merged filtered tweets for this iteration!'.format(len(pokemons)))
            for pokemon in pokemons:
                fb_client.send_message_to_poke_thread(pokemon)
            log.warning('Sent Facebook notifications (to your group) for all nearby pokemon!')

        time.sleep(SLEEP_SECS)
        log.warning('')


if __name__ == '__main__':
    while True:
        try:
            log.warning('Starting script!')
            main()
        except Exception:
            log.warning('Script failed! Will restart!', exc_info=True)
            time.sleep(SLEEP_SECS * 5)
