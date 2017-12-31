import time

import os
from pyicloud import PyiCloudService
from pyicloud.exceptions import PyiCloudFailedLoginException
from src.clients.fb_client import FbClient

if os.path.isfile('./src/credentials.py'):
    from src.credentials import APPLE_EMAIL, APPLE_PASSWORD, APPLE_COOKIE_DIRECTORY, IPHONE_NAME
else:
    APPLE_EMAIL = 'EMAIL@DOMAIN.COM'
    APPLE_PASSWORD = 'PASSWORD'
    APPLE_COOKIE_DIRECTORY = './PATH/TO/DIR'
    IPHONE_NAME = 'DEVICE_NAME'

SLEEP_SECS = 60


class AppleClient(PyiCloudService):
    def __init__(self, fb_client=FbClient(), **kwargs):
        kwargs['password'] = APPLE_PASSWORD
        kwargs['cookie_directory'] = APPLE_COOKIE_DIRECTORY
        super(AppleClient, self).__init__(APPLE_EMAIL, **kwargs)
        self.log = kwargs.get('log', None)

        if self.requires_2fa:
            if self.log:
                self.log.warning('Send your Apple verification code '
                                 'that you received via SMS to Facebook Messenger chat!')

            if not self.send_verification_code(self.trusted_devices[0]):
                raise PyiCloudFailedLoginException('Failed to send SMS to 2FA phone number!')

            time.sleep(SLEEP_SECS)  # Wait for 60 second to send the 2FA code in Messenger Chat.
            codes_2fa = fb_client.get_messages_from_poke_thread(limit=1)

            if not self.validate_verification_code(self.trusted_devices[0], codes_2fa[0].replace(' ', '')):
                raise PyiCloudFailedLoginException('Failed to validate 2FA code!')

    def get_location(self):
        self.authenticate()
        devices = [device for device in self.devices if IPHONE_NAME in device['name']]
        location = devices[0].location()
        return location['latitude'], location['longitude']
