import logging
from datetime import datetime, timedelta
import webapp2
from google.appengine.api import channel, users
from google.appengine.ext import ndb
from HelpRequest import HelpRequest, help_queue_key
from LabTA import LabTA, labta_key
import ConfigDefaults
import json
import ChannelManager


def get_json_queue():
    q = HelpRequest.query(ancestor=help_queue_key())
    q = q.filter(HelpRequest.been_helped == False)
    q = q.filter(HelpRequest.canceled == False)
    q = q.order(HelpRequest.request_datetime)
    q.fetch()
    queue = []
    for e in q:
        tmp = {}
        tmp['name'] = e.name
        tmp['email'] = e.netid
        tmp['help_msg'] = e.help_msg
        tmp['course'] = e.course
        queue.append(tmp)
    return json.dumps(queue)

class GetQueue(webapp2.RequestHandler):
    # returns the current queue as a JSON object
    # returns it on the requester's channel, NOT in response
    # assume the channel was already created
    def get(self):
        user = users.get_current_user()
        json_queue = get_json_queue()
        channel.send_message(user.email(), json_queue)

class AddToQueue(webapp2.RequestHandler):
    def post(self):
        user = users.get_current_user()
        q = HelpRequest.query(HelpRequest.in_queue == True,
                              HelpRequest.netid == user.email(),
                              ancestor=help_queue_key())
        if q.count() != 0:
            self.response.write('Unable to add to queue')
            return
        hr = HelpRequest(parent=help_queue_key())
        hr.netid = user.email()
        hr.name = self.request.get('name')
        hr.help_msg = self.request.get('help_msg')
        hr.course = self.request.get('course')
        hr.put()
        ChannelManager.queue_update()

class MarkAsHelped(webapp2.RequestHandler):
    def post(self):
        user = users.get_current_user()
        q = HelpRequest.query(HelpRequest.in_queue == True,
                              HelpRequest.netid == self.request.get('email'),
                              ancestor=help_queue_key())
        if q.count() != 1:
            logging.error("Database corrupted for user {}".format(user.email()))
            return
        hr = q.get()
        hr.been_helped = True
        hr.attending_ta = user.email()
        hr.put()
        ChannelManager.queue_update()
        ta = LabTA.query(LabTA.email == hr.attending_ta, ancestor=labta_key()).fetch()[0]
        ChannelManager.notify_request_accepted(hr.netid, ta.first_name, ta.img_path)

class CancelFromQueue(webapp2.RequestHandler):
    def post(self):
        user = users.get_current_user()
        q = HelpRequest.query(HelpRequest.in_queue == True,
                              HelpRequest.netid == self.request.get('email'),
                              ancestor=help_queue_key())
        if q.count() != 1:
            logging.error("Database corrupted for user {}".format(user.email()))
            return
        hr = q.get()
        hr.canceled = True
        hr.put()
        ChannelManager.queue_update()

# Currently this is pretty insecure, theoretically any user could just
# be a dick and hit the URL...
class ClearQueue(webapp2.RequestHandler):
    @ndb.toplevel
    def post(self):
        q = HelpRequest.query(HelpRequest.in_queue == True, ancestor=help_queue_key()).fetch()
        for hr in q:
            hr.canceled = True
            hr.put()
        ChannelManager.queue_update()
