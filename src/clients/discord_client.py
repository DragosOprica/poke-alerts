import logging
from datetime import datetime, timezone

import os
import requests
from collections import defaultdict
from dateutil import parser
from requests.exceptions import HTTPError

if os.path.isfile('./src/credentials.py'):
    from src.credentials import DISCORD_API_TOKEN, DISCORD_CHANNELS
else:
    DISCORD_API_TOKEN = 'REPLACE_TOKEN'
    DISCORD_CHANNELS = ['REPLACE_SERVER']

log = logging.getLogger('client.discord_client')
SLEEP_SECS = 60
MAX_MESSAGES_PER_REQUEST = 50


class DiscordClient(object):
    """
    This class is very shitty. I only made it to work bare bone for my use case. Treat is as a piece of crap.
    """
    _base_url = 'https://discordapp.com/api/v6'
    _user_url = '/users/{user}'
    _channel_messages_url = '/channels/{channel}/messages'

    @property
    def auth_header(self):
        return {'Authorization': self.token}

    def __init__(self, **kwargs):
        self.token = DISCORD_API_TOKEN
        self.channels = DISCORD_CHANNELS
        self._login()
        self.ttl = kwargs.get('ttl', 2 * SLEEP_SECS)
        self.since_pokemon_message = defaultdict(int)

    def _login(self):
        resp = requests.get(self._base_url + self._user_url.format(user='@me'), headers=self.auth_header)
        resp.raise_for_status()

    def _new_enough(self, message, now):
        message_time = parser.parse(message['timestamp'])
        return (now - message_time).total_seconds() < self.ttl

    def get_pokemon_messages(self):
        max_pokemon_message = defaultdict(int)
        all_messages = []
        for channel in self.channels:
            while True:
                log.warning('Fetching messages for channel: {} with max_id: {} and since_id: {}'.format(
                    channel, max_pokemon_message[channel], self.since_pokemon_message[channel]))

                try:
                    params = {'limit': MAX_MESSAGES_PER_REQUEST}
                    if max_pokemon_message[channel]:
                        params['before'] = max_pokemon_message[channel]
                    resp = requests.get(self._base_url + self._channel_messages_url.format(channel=channel),
                                        headers=self.auth_header)
                    resp.raise_for_status()
                    messages = [message for message in resp.json()
                                if int(message['id']) > self.since_pokemon_message[channel]]
                except (HTTPError, KeyError) as e:
                    log.warning('Failed to fetch messages for channel: '
                                '{} with max_id: {} and since_id: {}'.format(channel,
                                                                             max_pokemon_message[channel],
                                                                             self.since_pokemon_message[channel]),
                                exc_info=True)
                    messages = []

                if not messages:
                    log.warning('No more messages for screen_name: {}'.format(channel))
                    break

                max_pokemon_message[channel] = min([int(message['id']) for message in messages])
                self.since_pokemon_message[channel] = max([int(message['id']) for message in messages])

                log.warning('Successfully fetched {} messages'.format(len(messages)))
                now = datetime.now(timezone.utc)
                messages = [message for message in messages if self._new_enough(message, now)]
                if not messages:
                    log.warning('No more recent messages for channel: {}'.format(channel))
                else:
                    log.warning('Finalized message filter by recent time. Got {} for channel: {}'.format(
                        len(messages), channel))
                all_messages.extend(messages)

                if len(messages) != MAX_MESSAGES_PER_REQUEST:
                    break

        return all_messages
