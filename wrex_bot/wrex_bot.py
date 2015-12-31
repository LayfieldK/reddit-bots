#!/usr/bin/python
import praw
import pdb
import re
import os
from config_bot import *

# Check that the file that contains our username exists
if not os.path.isfile("config_bot.py"):
    print "You must create a config file with your username and password."
    print "Please see config_skel.py"
    exit(1)

# Create the Reddit instance
r = praw.Reddit(user_agent=config_bot.USER_AGENT)

# and login
r.login(REDDIT_USERNAME, REDDIT_PASS)

# Have we run this code before? If not, create an empty list
if not os.path.isfile("wrex_bot_comments_replied_to.txt"):
    comments_replied_to = []

# If we have run the code before, load the list of posts we have replied to
else:
    # Read the file into a list and remove any empty values
    with open("wrex_bot_comments_replied_to.txt", "r") as f:
        comments_replied_to = f.read()
        comments_replied_to = comments_replied_to.split("\n")
        comments_replied_to = filter(None, comments_replied_to)

# Get the top 15 values from our subreddit
subreddit = r.get_subreddit('KevinBotTest')
#for comment in praw.helpers.comment_stream(r, 'KevinBotTest', limit = 100, verbosity = 0):
for comment in subreddit.get_comments():
    print "checking comment " + comment.id
    # If we haven't replied to this comment before
    if comment.id not in comments_replied_to:
        # Do a case insensitive search
        if re.search("^Wrex\.?$", comment.body, re.IGNORECASE):
            # Reply to the post
            comment.reply("Shepard.")
            print "Bot replying to : ", comment.id

            # Store the current id into our list
            comments_replied_to.append(comment.id)

# Write our updated list back to the file
with open("wrex_bot_comments_replied_to.txt", "w") as f:
    for comment_id in comments_replied_to:
        f.write(comment_id + "\n")