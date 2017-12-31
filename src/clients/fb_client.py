import json
import time

import os
from fbchat import Client, ThreadType

if os.path.isfile('./src/credentials.py'):
    from src.credentials import FB_EMAIL, FB_PASSWORD, FB_COOKIE_FILE, FB_THREAD_ID
else:
    FB_EMAIL = 'EMAIL@DOMAIN.COM'
    FB_PASSWORD = 'PASSWORD'
    FB_COOKIE_FILE = './PATH/TO/FILE'
    FB_THREAD_ID = '1234567890987654'

if os.path.isfile(FB_COOKIE_FILE):
    with open(FB_COOKIE_FILE, 'r') as f:
        SESSION_COOKIES = json.load(f)
else:
    SESSION_COOKIES = None

SLEEP_SECS = 60


class FbClient(Client):
    def __init__(self, **kwargs):
        kwargs['session_cookies'] = SESSION_COOKIES
        super(FbClient, self).__init__(FB_EMAIL, FB_PASSWORD, **kwargs)  # Log in with our email, password and cookies.
        with open(FB_COOKIE_FILE, 'w') as g:  # Then, if login is successful, update the cookies file.
            json.dump(self.getSession(), g)
        self.log = kwargs.get('log', None)

    def on2FACode(self):
        if self.log:
            self.log.warning('Go to your Facebook account and approve this login attempt!')
        time.sleep(SLEEP_SECS)  # Wait for 60 second to acknowledge the login from another device/browser.
        return ''  # Then return an empty string since we're already confirmed 2FA.

    def get_messages_from_poke_thread(self, limit=5):
        messages = self.fetchThreadMessages(FB_THREAD_ID, limit=limit)
        return [message.text for message in messages if message.text]

    def send_message_to_poke_thread(self, message):
        return self.sendMessage(message, thread_id=FB_THREAD_ID, thread_type=ThreadType.GROUP)
