#!/usr/bin/python
import praw
import pdb
import re
import os
import datetime
import time
import traceback
import urllib
import urllib2
from peewee import *
from peewee import OperationalError
from peewee import DoesNotExist
from bs4 import BeautifulSoup
from steampowered_config import *

# Verify that config file is present in current directory
if not os.path.isfile("steampowered_config.py"):
    print "Config file not found in current directory."
    exit(1)

db = SqliteDatabase('steampowered.db')
comments_replied_to=[]  

# Create Reddit object
r = praw.Reddit(user_agent=USER_AGENT)

# Login with credentials from config file
r.login(REDDIT_USERNAME, REDDIT_PASS)

subreddit = r.get_subreddit('KevinBotTest')

def initialize_db():
    print "db opening"
    db.connect()
    try:
        db.create_tables([reply, comment_reply, submission_reply])
        print "db opened"
    except OperationalError:
        # Table already exists. Do nothing
        pass

def deinit():
    db.close()
    print "db closed"
    

class reply(Model):
    date_of_reply = DateTimeField()
    user = CharField()
    subreddit = CharField()
    steamapp_id = CharField()
    
    class Meta:
        database = db
    
class comment_reply(Model):
    reply = ForeignKeyField(reply, related_name='comment_replies')
    comment_id = CharField()
    
    class Meta:
        database = db

def is_already_replied(comment_id):
    if comment_id in comments_replied_to:
        return True
    try:
        comment_reply.select().where(
            comment_reply.comment_id == comment_id).get()
        return True
    except DoesNotExist:
        return False
    
class submission_reply(Model):
    reply = ForeignKeyField(reply, related_name='submission_replies')
    submission_id = CharField()
    
    class Meta:
        database = db

def get_date(comment):
    time = comment.created
    return datetime.datetime.fromtimestamp(time)

def post_reply():
    return
  
def get_steamapp_ids(comment_body):
    # receives goodreads url
    # returns the id using regex
    regex = "http://store\.steampowered\.com/app/(.*)/"
    return set(re.findall(regex, comment_body))


def get_steamapp_details(steamapp_id):
    print steamapp_id
    
    steamapp_data = {}
    url = "http://store.steampowered.com/app/" + steamapp_id
    
    opener = urllib2.build_opener()
    opener.addheaders.append(('Cookie', 'birthtime=852094801'))
    html = opener.open(url)
    bsObj = BeautifulSoup( html.read())
    
    title_obj = bsObj.find("div", class_="apphub_AppName")
    steamapp_data['title'] = title_obj.text.strip()
    print title_obj.text.strip()
    
    game_desc_obj = bsObj.find("div", class_="game_description_snippet")
    steamapp_data['game_desc'] = game_desc_obj.text.strip()
    print game_desc_obj.text.strip()
    
    details_block = bsObj.find("div", class_="details_block")

    for br in details_block.findAll('br'):
        br.extract()
    
    genrePattern = re.compile(r'Genre:')
    steamapp_data['genre'] = details_block.find('b', text=genrePattern).find_next_sibling().text.strip()
    print details_block.find('b', text=genrePattern).find_next_sibling().text.strip()
    
    devPattern = re.compile(r'Developer:')
    steamapp_data['developer'] = details_block.find('b', text=devPattern).find_next_sibling().text.strip()
    print details_block.find('b', text=devPattern).find_next_sibling().text.strip()
    
    pubPattern = re.compile(r'Publisher:')
    steamapp_data['publisher'] = details_block.find('b', text=pubPattern).find_next_sibling().text.strip()
    print details_block.find('b', text=pubPattern).find_next_sibling().text.strip()
    
    releaseDatePattern = re.compile(r'Release Date:')
    steamapp_data['release_date'] = details_block.find('b', text=releaseDatePattern).next_sibling.strip()
    
    
    game_review_summary_obj = bsObj.find("span", class_="game_review_summary")
    steamapp_data['game_review_summary'] = game_review_summary_obj.text.strip()
    print game_review_summary_obj.text.strip()
    
    glance_ctn = bsObj.find("div",class_="glance_ctn_responsive_left")
    steamapp_data['game_review_stats'] = glance_ctn.div["data-store-tooltip"].strip()
    print glance_ctn.div["data-store-tooltip"].strip()
    
    tag_objects = bsObj.find("div", class_="glance_tags popular_tags").find_all("a")
    tags = []
                    
    for tag_object in tag_objects:
        tags.append(tag_object.text.strip())
    
    steamapp_data['tags'] = ", ".join(tags)
        
    price_section = bsObj.find("div", class_="game_purchase_action")
    steamapp_data['current_price'] = ""
    steamapp_data['original_price'] = ""
    steamapp_data['discount_percentage'] = ""
    if price_section.find("div", class_="game_purchase_price"):
        steamapp_data['current_price'] = price_section.find("div", class_="game_purchase_price").text.strip()
    elif price_section.find("div", class_="discount_original_price"):
        steamapp_data['current_price'] = price_section.find("div", class_="discount_final_price").text.strip()
        steamapp_data['original_price'] = price_section.find("div", class_="discount_original_price").text.strip()
        steamapp_data['discount_percentage'] = price_section.find("div", class_="discount_pct").text.strip().replace("-","")
    else :
        steamapp_data['current_price'] = "N/A"
    return steamapp_data

def add_steamapp_details_to_reply(reply_text,steamapp_data):
    reply_text +=  "|||\n"
    reply_text += "|:--|:--|\n"
    reply_text += "|Name|" + steamapp_data['title'] + "|\n"
    reply_text += "|Description|" + steamapp_data['game_desc'] + "|\n"
    reply_text += "|Price|" 
    
    if steamapp_data['discount_percentage'] == "" :
        reply_text += steamapp_data['current_price'] + "|\n"
    else :
        reply_text += steamapp_data['original_price'] + "  -  " + steamapp_data['discount_percentage'] + "  =  " + steamapp_data['current_price'] + "|\n"
        
    reply_text += "|Steam Reviews|" + steamapp_data['game_review_summary'] + " - " + steamapp_data['game_review_stats'] + "|\n"
    reply_text += "|Popular Tags|" + steamapp_data['tags'] + "|\n"
    reply_text += "|Developer|" + steamapp_data['developer'] + "|\n"
    reply_text += "|Publisher|" + steamapp_data['publisher'] + "|\n"
    reply_text += "|Release Date|" + steamapp_data['release_date'] + "|\n"
    reply_text += "\n\n"
    return reply_text

def process_reply_to_comment(comment):
    print "Bot replying to : ", comment.id              
    steamapps = get_steamapp_ids(comment.body)
    reply_text = ""
    for steamapp in steamapps:
        steamapp_data = get_steamapp_details(steamapp)
        reply_text = add_steamapp_details_to_reply(reply_text,steamapp_data)
        
    post_reply_to_comment(comment,reply_text,steamapp)    
    print "finished"
    
def post_reply_to_comment(comment,reply_text,steamapp_id):
    comment.reply(reply_text)
    
    reply_data = reply(user=comment.author,
                       date_of_reply=datetime.datetime.utcnow(),
                       subreddit=comment.submission.subreddit,
                       steamapp_id=steamapp_id)
    reply_data.save()
    
    comment_replied_to = comment_reply(reply=reply_data,
                                       comment_id=comment.id)
    comment_replied_to.save()
    comments_replied_to.append(comment.id)

def main():
        
    # Designate working subreddit to search through
    
    continueLoop = True
    #while continueLoop:
    # Super basic error handling for now.  Only exists so that if something goes wrong in the middle
    # of running, comments that were replied to are still recorded
    try:
        # Gets all recent comments in subreddit
        for comment in subreddit.get_comments(limit=None):
            print "checking comment " + comment.id
            # If this comment has not already been replied to by this bot
              
            if not is_already_replied(comment.id):
                #if comment.author != None and comment.author.name != "steampowered_bot":
                if comment.author != None:
                    if "store.steampowered.com/app" in comment.body:
                        process_reply_to_comment(comment)       

    except Exception as e:
        traceback.print_exc()
        print str(e)
        continueLoop = False
            
initialize_db()
main()
deinit()
        
