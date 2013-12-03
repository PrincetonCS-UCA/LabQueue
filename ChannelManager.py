import logging
import webapp2
from google.appengine.api import channel, memcache
import QueueManager

SUBSCRIBERS_KEY = 'subscribers'

def add_sub(sub):
    client = memcache.Client()
    if client.get(SUBSCRIBERS_KEY) is None:
        client.add(SUBSCRIBERS_KEY, set())
    while True:
        s = client.gets(SUBSCRIBERS_KEY)
        s.add(sub)
        logging.info(s)
        if client.cas(SUBSCRIBERS_KEY, s):
            break

def remove_sub(sub):
    client = memcache.Client()
    while True:
        s = client.gets(SUBSCRIBERS_KEY)
        try:
            s.remove(sub)
        except:
            break
        if client.cas(SUBSCRIBERS_KEY, s):
            break

class SubscriberConnect(webapp2.RequestHandler):
    def post(self):
        logging.info("connect")
        add_sub(self.request.get('from'))

class SubscriberDisconnect(webapp2.RequestHandler):
    def post(self):
        logging.info("disconnect")
        remove_sub(self.request.get('from'))

def queue_update(help_request):
    json_queue = QueueManager.get_json_queue()
    logging.info("sending  notifications")
    subs = memcache.get(SUBSCRIBERS_KEY)
    for s in subs:
        channel.send_message(s, json_queue)

