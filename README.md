## Custom location based script for Pokemon Alerts

This script reads feeds of pokemon from Twitter and/or Discord regularly 
and then filters those by your iPhone's location and sends Messenger
notifications of the ones close to your location.

### Instalation
```bash
$ virtualenv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
```

### Prerequisites
This script makes some assumptions:
* You have access to Twitter, Discord, Facebook and iCloud
* You have Twitter feeds of tweets that include a Pokemon name in 
its text and a location (latitude, longitude) in its URL
  * Any other tweet will be discarded
* You have Discord channels of messages that include a Pokemon name in 
its text and a location (latitude, longitude) in its URL
  * Any other message will be discarded

You need to create a file that it's not tracked because of sensitive 
information (login credentials and tokens) located at `src/credentials.py`.
The file should look like this:
```python

FB_EMAIL = 'mail@domain.com'
FB_PASSWORD = 'password'
FB_THREAD_ID = '1525064787606453'
FB_COOKIE_FILE = './cookies/fb'

APPLE_EMAIL = 'mail@domain.com'
APPLE_PASSWORD = 'password'
APPLE_COOKIE_DIRECTORY = './cookies/apple'
IPHONE_NAME = "John's iPhone"

TWITTER_API_CONSUMER_KEY = 'key'
TWITTER_API_CONSUMER_SECRET = 'secret'
TWITTER_API_ACCESS_TOKEN_KEY = 'token-key'
TWITTER_API_ACCESS_TOKEN_SECRET = 'token-secret'
TWITTER_POKEMON_FEEDS = [
  'username',
]

DISCORD_API_TOKEN = 'token'
DISCORD_CHANNELS = [
  'channel_id',
]

POKEMON_LIST = [
  'Dragonite',
]
```
* The script uses the `FB` info to login to Facebook and send 
messages from that account to that group thread.
* The script uses the `APPLE` info to login to iCloud and get 
the location of that device.
* The script uses the `TWITTER` info to togin to Twitter and 
fetch the tweets of those feeds.
* The script uses the `DISCORD` info to fetch Discord messages 
from those channels with that token.
* `POKEMON_LIST` should contain all pokemon names, but since 
it's too long I didn't put it here.

The script uses a cookies folder to save login info, so if 
you're using the same paths for cookies as my example,
don't forget to create the folder (that is also ignored in git)
```bash
mkdir cookies
```

### Run
```bash
$ PYTHONPATH=. python src/script.py
```
