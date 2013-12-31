import logging
import webapp2
from google.appengine.api import channel, memcache
import QueueManager
import json
import LabTA

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

def queue_update():
    json_queue = QueueManager.get_json_queue()
    logging.info("sending notifications")
    subs = memcache.get(SUBSCRIBERS_KEY)
    msg = json.dumps({'type': 'queue', 'data': json_queue, 'active_tas': LabTA.update_active_tas()})
    for s in subs:
        channel.send_message(s, msg)

def notify_request_accepted(student_email, ta_name, img_path):
    data = json.dumps({'name': ta_name, 'img': img_path})
    msg = json.dumps({'type': 'request_ack', 'data': data})
    channel.send_message(student_email, msg)
