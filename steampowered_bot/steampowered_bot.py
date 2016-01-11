#!/usr/bin/python
import praw
from prawoauth2 import PrawOAuth2Mini
import pdb
import re
import os
import datetime
import time
import traceback
import urllib
import urllib2
import logging
from peewee import *
from peewee import OperationalError
from peewee import DoesNotExist
from bs4 import BeautifulSoup
from steampowered_config import *

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

logfile_name = "steampowered_bot_" + time.strftime("%m-%d-%Y") + ".log"
handler = logging.FileHandler(logfile_name)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

logger.info("steampowered_bot started")

# Verify that config file is present in current directory
if not os.path.isfile("steampowered_config.py"):
    logger.error("Config file not found in current directory.")
    exit(1)

db = SqliteDatabase('steampowered.db')
comments_replied_to=[] 

# Create Reddit object
r = praw.Reddit(user_agent=USER_AGENT)

# Login with credentials from config file
#r.login(REDDIT_USERNAME, REDDIT_PASS)
try:
    oauth_helper = PrawOAuth2Mini(r, app_key=APPKEY,
                              app_secret=APPSECRET, access_token=ACCESSTOKEN,
                              scopes=SCOPES, refresh_token=REFRESHTOKEN) 
except praw.errors.OAuthInvalidToken:
    logger.warn("Invalid OAuth Token.")
    refresh_oauth() 

subreddit = r.get_subreddit('KevinBotTest')

def refresh_oauth():
    logger.info("Attempting to refresh refresh token.")
    oauth_helper.refresh()
    logger.info("Token refreshed.")
    oauth_helper = PrawOAuth2Mini(r, app_key=APPKEY,
                              app_secret=APPSECRET, access_token=ACCESSTOKEN,
                              scopes=SCOPES, refresh_token=REFRESHTOKEN) 

def initialize_db():
    logger.info("db connecting")
    db.connect()
    try:
        db.create_tables([reply, reply_steamapp, comment_reply, submission_reply, banned_user])
        logger.info("db opened")
    except OperationalError:
        # Table already exists. Do nothing
        pass

def deinit():
    db.close()
    logger.info("db closed")
    

class reply(Model):
    date_of_reply = DateTimeField()
    user = CharField()
    subreddit = CharField()
    
    class Meta:
        database = db

class reply_steamapp(Model):
    reply = ForeignKeyField(reply, related_name='reply_steamapps')
    steamapp_id = CharField()
    
    class Meta:
        database = db
    
class comment_reply(Model):
    reply = ForeignKeyField(reply, related_name='comment_replies')
    comment_id = CharField()
    
    class Meta:
        database = db

class submission_reply(Model):
    reply = ForeignKeyField(reply, related_name='submission_replies')
    submission_id = CharField()
    
    class Meta:
        database = db
        
class banned_user(Model):
    username = CharField()
    
    class Meta:
        database = db
  
def is_already_replied(comment_id):
    if comment_id in comments_replied_to:
        return True
    try:
        comment_reply.select().where(comment_reply.comment_id == comment_id).get()
        return True
    except DoesNotExist:
        return False
    
def is_banned_user(username):
    try:
        banned_user.select().where(banned_user.username == username).get()
        return True
    except DoesNotExist:
        return False
    
def has_reached_postlimit():
    posts_within_hour = reply.select().where(reply.date_of_reply > datetime.datetime.utcnow() + datetime.timedelta(hours=-1)).count()
    if posts_within_hour >= POSTLIMIT:
        return True
    else:
        return False
    
def get_date(comment):
    time = comment.created
    return datetime.datetime.fromtimestamp(time)

def get_steamapp_ids(comment_body):
    # receives goodreads url
    # returns the id using regex
    regex = "http://store\.steampowered\.com/app/(.*?)[/\s\.\?]"
    return re.findall(regex, comment_body)

def get_steamapp_details(steamapp_id):
    logger.info("getting details for steamapp %s", steamapp_id)
    
    steamapp_data = {}
    url = "http://store.steampowered.com/app/" + steamapp_id
    
    opener = urllib2.build_opener()
    opener.addheaders.append(('Cookie', 'birthtime=852094801'))
    html = opener.open(url)
    bsObj = BeautifulSoup( html.read())
    
    title_obj = bsObj.find("div", class_="apphub_AppName")
    steamapp_data['title'] = title_obj.get_text().strip()
        
    game_desc_obj = bsObj.find("div", class_="game_description_snippet")
    if game_desc_obj:
        steamapp_data['game_desc'] = game_desc_obj.get_text().strip()
    
    details_block = bsObj.find("div", class_="details_block")

    for br in details_block.findAll('br'):
        br.extract()
    
    genre_pattern = re.compile(r'Genre:')
    genre_label = details_block.find('b', text=genre_pattern)
    if genre_label:
        genre_objects = genre_label.find_next_siblings("a", href=re.compile("genre"))
        genres = []     
        for genre_object in genre_objects:
            genres.append(genre_object.get_text().strip())
        steamapp_data['genre'] = ", ".join(genres)
        
    dev_pattern = re.compile(r'Developer:')
    dev_label = details_block.find('b', text=dev_pattern)
    if dev_label:
        steamapp_data['developer'] = dev_label.find_next_sibling().get_text().strip()
        
    pub_pattern = re.compile(r'Publisher:')
    pub_label = details_block.find('b', text=pub_pattern)
    if pub_label:
        steamapp_data['publisher'] = pub_label.find_next_sibling().get_text().strip()
        
    release_date_pattern = re.compile(r'Release Date:')
    release_date_label = details_block.find('b', text=release_date_pattern)
    if release_date_label:
        steamapp_data['release_date'] = release_date_label.next_sibling.strip()
    
    runtime_pattern = re.compile(r'Running Time:')
    runtime_label = details_block.find('b', text=runtime_pattern)
    if runtime_label:
        steamapp_data['running_time'] = runtime_label.next_sibling.strip()
        
    production_pattern = re.compile(r'Production:')
    production_label = details_block.find('b', text=production_pattern)
    if production_label:
        steamapp_data['production'] = production_label.find_next_sibling().get_text().strip()
        
    manufacturer_pattern = re.compile(r'Manufacturer:')
    manufacturer_label = details_block.find('b', text=manufacturer_pattern)
    if manufacturer_label:
        steamapp_data['manufacturer'] = manufacturer_label.find_next_sibling().get_text().strip()
        
    
    game_review_summary_obj = bsObj.find("span", class_="game_review_summary")
    if game_review_summary_obj:
        steamapp_data['game_review_summary'] = game_review_summary_obj.get_text().strip()
    
    glance_ctn = bsObj.find("div",class_="glance_ctn_responsive_left")
    if glance_ctn:
        glance_ctn_divs = bsObj.find_all("div")
        for div in glance_ctn_divs:
            if div.has_attr("data-store-tooltip"):
                steamapp_data['game_review_stats'] = div["data-store-tooltip"]
                break
    
    tags_root = bsObj.find("div", class_="glance_tags popular_tags")
    tag_objects=[]
    if tags_root:
        tag_objects = tags_root.find_all("a")
    tags = []
                    
    for tag_object in tag_objects:
        tags.append(tag_object.get_text().strip())
    
    steamapp_data['tags'] = ", ".join(tags)
        
    price_section = bsObj.find("div", class_="game_purchase_action")
    steamapp_data['current_price'] = ""
    steamapp_data['original_price'] = ""
    steamapp_data['discount_percentage'] = ""
    if price_section:
        if price_section.find("div", class_="game_purchase_price"):
            steamapp_data['current_price'] = price_section.find("div", class_="game_purchase_price").get_text().strip()
        elif price_section.find("div", class_="discount_original_price"):
            steamapp_data['current_price'] = price_section.find("div", class_="discount_final_price").get_text().strip()
            steamapp_data['original_price'] = price_section.find("div", class_="discount_original_price").get_text().strip()
            steamapp_data['discount_percentage'] = price_section.find("div", class_="discount_pct").get_text().strip().replace("-","")
        else :
            steamapp_data['current_price'] = "N/A"
    else:
        steamapp_data['current_price'] = "N/A"
    return steamapp_data

def add_steamapp_details_to_reply(reply_text,steamapp_data):
    reply_text +=  "|||\n"
    reply_text += "|:--|:--|\n"
    reply_text += "|**Name**|**" + steamapp_data['title'] + "**|\n"
    if "game_desc" in steamapp_data:
        reply_text += "|**Description**|" + steamapp_data['game_desc'] + "|\n"
    if "genre" in steamapp_data:
        reply_text += "|**Genre**|" + steamapp_data['genre'] + "|\n"
    if "running_time" in steamapp_data:
        reply_text += "|**Running Time**|" + steamapp_data['running_time'] + "|\n"
    reply_text += "|**Price**|" 
    
    if steamapp_data['discount_percentage'] == "" :
        reply_text += steamapp_data['current_price'] + "|\n"
    else :
        reply_text += "~~" + steamapp_data['original_price'] + "~~  -  " + steamapp_data['discount_percentage'] + "  =  **" + steamapp_data['current_price'] + "**|\n"
    
    if "game_review_summary" in steamapp_data:    
        reply_text += "|**Steam Reviews**|" + steamapp_data['game_review_summary'] + " - " + steamapp_data['game_review_stats'] + "|\n"
    if "tags" in steamapp_data:
        reply_text += "|**Popular Tags**|" + steamapp_data['tags'] + "|\n"
    if "developer" in steamapp_data:
        reply_text += "|**Developer**|" + steamapp_data['developer'] + "|\n"
    if "publisher" in steamapp_data:
        reply_text += "|**Publisher**|" + steamapp_data['publisher'] + "|\n"
    if "manufacturer" in steamapp_data:
        reply_text += "|**Manufacturer**|" + steamapp_data['manufacturer'] + "|\n"
    if "production" in steamapp_data:
        reply_text += "|**Production**|" + steamapp_data['production'] + "|\n"
    if "release_date" in steamapp_data:
        reply_text += "|**Release Date**|" + steamapp_data['release_date'] + "|\n"
    reply_text += "\n&nbsp;\n***\n\n"
    return reply_text

def process_reply_to_comment(comment):
    logger.info("Bot replying to : %s", comment.id)              
    steamapps = get_steamapp_ids(comment.body)
    reply_text = ""
    steamapp_index = 0
    for steamapp in steamapps:
        if steamapp_index < 10:
            steamapp_data = get_steamapp_details(steamapp)
            reply_text = add_steamapp_details_to_reply(reply_text,steamapp_data)
            steamapp_index+=1
        else:
            break
    
    reply_text += "^^I ^^am ^^a ^^bot ^^created ^^for ^^fun. ^^Send ^^comments, ^^suggestions, ^^and ^^other ^^feedback ^^to ^^" + CREATOR_USER_PAGE + "."    
    post_reply_to_comment(comment,reply_text,steamapps)    
    logger.info("comment %s replied to", comment.id)
    
def post_reply_to_comment(comment,reply_text,steamapp_ids):
    comment.reply(reply_text)
    update_db_with_reply(comment,steamapp_ids)
    
    
def update_db_with_reply(comment, steamapp_ids):
    reply_data = reply(user=comment.author,
                       date_of_reply=datetime.datetime.utcnow(),
                       subreddit=comment.submission.subreddit)
    reply_data.save()
    
    for steamapp_id in steamapp_ids:
        reply_steamapp_data = reply_steamapp(reply=reply_data,steamapp_id=steamapp_id)
        reply_steamapp_data.save()
    
    comment_replied_to = comment_reply(reply=reply_data,
                                       comment_id=comment.id)
    comment_replied_to.save()
    comments_replied_to.append(comment.id)

def main():
    continueLoop = True
    while continueLoop:
        # Super basic error handling for now.  Only exists so that if something goes wrong in the middle
        # of running, comments that were replied to are still recorded
        try:
            # Gets all recent comments in subreddit
            for comment in praw.helpers.comment_stream(r,subreddit=SUBREDDIT,limit=None,verbosity=0):
                try:
                    logger.info("checking comment %s", comment.id)
                    # If this comment has not already been replied to by this bot
                    if not has_reached_postlimit():  
                        if not is_already_replied(comment.id):
                            if comment.author != None and comment.author.name != REDDIT_USERNAME:
                                if get_date(comment) > datetime.datetime.now() + datetime.timedelta(days=-1):
                                    if "store.steampowered.com/app" in comment.body:
                                        process_reply_to_comment(comment) 
                                else:
                                    logger.info("comment %s older than a day", comment.id)      
                        else:
                            logger.info("comment %s already replied to", comment.id)
                    else:
                        logger.info("reached post limit, ignoring comments")
                except praw.errors.OAuthInvalidToken:
                    logger.warn("Invalid OAuth Token.")
                    refresh_oauth() 
                except Exception as e:
                    traceback.print_exc()
                    print str(e)
                    logger.error(str(e))
        except praw.errors.OAuthInvalidToken:
            logger.warn("Invalid OAuth Token.")
            refresh_oauth() 
        except KeyboardInterrupt:
            deinit()
            raise
        except Exception as e:
            traceback.print_exc()
            print str(e)
            #continueLoop = False
            logger.error(str(e))
            

initialize_db()
main()
deinit()

        
