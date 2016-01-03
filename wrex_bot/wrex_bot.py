#!/usr/bin/python
import praw
import pdb
import re
import os
import datetime
import time
import traceback
from wrex_config import *

def get_date(comment):
    time = comment.created
    return datetime.datetime.fromtimestamp(time)


# Verify that config file is present in current directory
if not os.path.isfile("wrex_config.py"):
    print "Config file not found in current directory."
    exit(1)

# Create Reddit object
r = praw.Reddit(user_agent=USER_AGENT)

# Login with credentials from config file
r.login(REDDIT_USERNAME, REDDIT_PASS)

# If file with replied to comments does not exist, then create empty array to store them in
if not os.path.isfile("wrex_bot_comments_replied_to.txt"):
    comments_replied_to = []

# otherwise, load replied to comments from existing file
else:
    # Read the file into a list and remove any empty values
    with open("wrex_bot_comments_replied_to.txt", "r") as f:
        comments_replied_to = f.read()
        comments_replied_to = comments_replied_to.split("\n")
        comments_replied_to = filter(None, comments_replied_to)

# Designate working subreddit to search through
subreddit = r.get_subreddit('all')
continueLoop = True
while continueLoop:
    # Super basic error handling for now.  Only exists so that if something goes wrong in the middle
    # of running, comments that were replied to are still recorded
    try:
        # Gets all recent comments in subreddit
        for comment in subreddit.get_comments(limit=None):
            print "checking comment " + comment.id
            if get_date(comment) > datetime.datetime.now() + datetime.timedelta(minutes=-1):
            # If this comment has not already been replied to by this bot
                if comment.id not in comments_replied_to:
                    # Use regex to see if the body of the comment is 'Wrex' or 'Wrex.'  (case insensitive)
                    if re.search("^Wrex\.?$", comment.body, re.IGNORECASE):
                        # Reply with 'Shepard.'
                        comment.reply("Shepard.")
                        print "Bot replying to : ", comment.id
            
                        # Add replied to comment to our array of comments
                        comments_replied_to.append(comment.id)
    except Exception as e:
        traceback.print_exc()
        print str(e)
        continueLoop = False
    # Rewrite the text file containing comments that the bot has replied to
    with open("wrex_bot_comments_replied_to.txt", "w") as f:
        for comment_id in comments_replied_to:
            f.write(comment_id + "\n")
            
    time.sleep(WAIT)
        
