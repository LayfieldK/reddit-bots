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

db = SqliteDatabase('steampowered.db')
comments_replied_to=[]  

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

def search_for_steam_links():
    return

def load_data():
    return
    
def post_reply():
    return
    
def retrieve_steam_url():
    return

def reddify(html):
  global has_list
  if re.search('&lt;li&gt;',html):
    has_list = True
  else:
    has_list = False
  html = html.replace('&lt;b&gt;', '__')
  html = html.replace('&lt;/b&gt;', '__')
  html = html.replace('&lt;i&gt;', '*')
  html = html.replace('&lt;/i&gt;', '*')
  if '__*' in html and '*__' in html:
    html = html.replace('__*', '___')
    html = html.replace('*__', '___')
  html = re.sub('&lt;sup&gt;','^',html)
  html = re.sub('&lt;sup.*?&gt;',' ',html)
  html = html.replace('&lt;/sup&gt;','')
  html = html.replace('&lt;dt&gt;','&lt;p&gt;')
  html = html.replace('&lt;/dt&gt;','&lt;/p&gt;')
  html = html.replace('&lt;ul&gt;','&lt;p&gt;')
  html = html.replace('&lt;/ul&gt;','&lt;/p&gt;')
  html = html.replace('&lt;ol&gt;','&lt;p&gt;')
  html = html.replace('&lt;/ol&gt;','&lt;/p&gt;')
  html = html.replace('&lt;dd&gt;','&lt;p&gt;>')
  html = html.replace('&lt;/dd&gt;','&lt;/p&gt; ')
  html = html.replace('&lt;li&gt;','&lt;p&gt;* ')
  html = html.replace('&lt;/li&gt;','&lt;/p&gt;')
  html = html.replace('&lt;blockquote&gt;','&lt;p&gt;>')
  html = html.replace('&lt;/blockquote&gt;','&lt;/p&gt; ')
  return html
  


# Verify that config file is present in current directory
if not os.path.isfile("steampowered_config.py"):
    print "Config file not found in current directory."
    exit(1)

# Create Reddit object
r = praw.Reddit(user_agent=USER_AGENT)

# Login with credentials from config file
r.login(REDDIT_USERNAME, REDDIT_PASS)

def main():
        
    # Designate working subreddit to search through
    subreddit = r.get_subreddit('KevinBotTest')
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
                
                regexSerch = re.search("http://store\.steampowered\.com/app/(.*)/", comment.body, re.IGNORECASE)
                if regexSerch:
                    print "match"
                    url = regexSerch.group(0)
                    html = urllib2.urlopen(url) 
                    bsObj = BeautifulSoup( html.read())
                    
                    title_obj = bsObj.find("div", class_="apphub_AppName")
                    title = title_obj.text.strip()
                    print title_obj.text.strip()
                    
                    game_desc_obj = bsObj.find("div", class_="game_description_snippet")
                    game_desc = game_desc_obj.text.strip()
                    print game_desc_obj.text.strip()
                    
                    details_block = bsObj.find("div", class_="details_block")
                    
                    
                    
                    for br in details_block.findAll('br'):
                        br.extract()
                    
                    genrePattern = re.compile(r'Genre:')
                    genre = details_block.find('b', text=genrePattern).find_next_sibling().text.strip()
                    print details_block.find('b', text=genrePattern).find_next_sibling().text.strip()
                    
                    devPattern = re.compile(r'Developer:')
                    developer = details_block.find('b', text=devPattern).find_next_sibling().text.strip()
                    print details_block.find('b', text=devPattern).find_next_sibling().text.strip()
                    
                    pubPattern = re.compile(r'Publisher:')
                    publisher = details_block.find('b', text=pubPattern).find_next_sibling().text.strip()
                    print details_block.find('b', text=pubPattern).find_next_sibling().text.strip()
                    
                    releaseDatePattern = re.compile(r'Release Date:')
                    release_date = details_block.find('b', text=releaseDatePattern).next_sibling.strip()
                    print release_date
                    
                    game_review_summary_obj = bsObj.find("span", class_="game_review_summary")
                    game_review_summary = game_review_summary_obj.text.strip()
                    print game_review_summary_obj.text.strip()
                    
                    glance_ctn = bsObj.find("div",class_="glance_ctn_responsive_left")
                    game_review_stats = glance_ctn.div["data-store-tooltip"].strip()
                    print glance_ctn.div["data-store-tooltip"].strip()
                    
                    tag_objects = bsObj.find("div", class_="glance_tags popular_tags").find_all("a")
                    tags = []
                                    
                    for tag_object in tag_objects:
                        tags.append(tag_object.text.strip())
                    
                        
                    price_section = bsObj.find("div", class_="game_purchase_action")
                    current_price = ""
                    original_price = ""
                    discount_percentage = ""
                    if price_section.find("div", class_="game_purchase_price"):
                        current_price = price_section.find("div", class_="game_purchase_price").text.strip()
                    elif price_section.find("div", class_="discount_original_price"):
                        current_price = price_section.find("div", class_="discount_final_price").text.strip()
                        original_price = price_section.find("div", class_="discount_original_price").text.strip()
                        discount_percentage = price_section.find("div", class_="discount_pct").text.strip().replace("-","")
                    else :
                        current_price = "N/A"
                    
                    print "Bot replying to : ", comment.id
                    
                    reply_text =  "|||\n"
                    reply_text += "|:--|:--|\n"
                    reply_text += "|Name|" + title + "|\n"
                    reply_text += "|Description|" + game_desc + "|\n"
                    reply_text += "|Price|" 
                    
                    if discount_percentage == "" :
                        reply_text += current_price + "|\n"
                    else :
                        reply_text += original_price + "  -  " + discount_percentage + "  =  " + current_price + "|\n"
                        
                    reply_text += "|Steam Reviews|" + game_review_summary + " - " + game_review_stats + "|\n"
                    reply_text += "|Popular Tags|"
                    
                    reply_text += ", ".join(tags)
                        
                    reply_text += "|\n"
                    reply_text += "|Developer|" + developer + "|\n"
                    reply_text += "|Publisher|" + publisher + "|\n"
                    reply_text += "|Release Date|" + release_date + "|\n"
                    
                    comment.reply(reply_text)
                    
                    reply_data = reply(user=comment.author,
                                       subreddit=comment.submission.subreddit,
                                       steamapp_id=regexSerch.group(1))
                    reply_data.save()
                    
                    comment_replied_to = comment_reply(reply=reply_data,
                                                       comment_id=comment.id)
                    comment_replied_to.save()
                    comments_replied_to.append(comment.id)
                    print "finished"        
                    # Add replied to comment to our array of comments
                    #comments_replied_to.append(comment.id)
    except Exception as e:
        traceback.print_exc()
        print str(e)
        continueLoop = False
            
#time.sleep(WAIT)

initialize_db()
main()
deinit()
        
