#!/usr/bin/env python

# this meant to be run once only, for a bot as recommended here -
# https://github.com/avinassh/prawoauth2
# taken from example here -
# https://github.com/avinassh/prawoauth2/blob/master/examples/halflife3-bot/onetime.py

import praw
from prawoauth2 import PrawOAuth2Server

from steampowered_config import *

reddit_client = praw.Reddit(user_agent=USER_AGENT)
oauthserver = PrawOAuth2Server(reddit_client, app_key=APPKEY,
                               app_secret=APPSECRET, state=USER_AGENT,
                               scopes=SCOPES)

# start the server, this will open default web browser
# asking you to authenticate
oauthserver.start()
print(oauthserver.get_access_codes())