import logging
from datetime import datetime, timedelta
import webapp2
from google.appengine.api import channel, users, memcache
from google.appengine.ext import ndb
from HelpRequest import HelpRequest, help_queue_key
from LabTA import LabTA, labta_key, is_ta, update_active_tas, get_active_tas
import json
import ChannelManager

def get_locations():
    friend = {'name': 'Friend Center', 'id': 'FriendCenter'}
    frist = {'name': 'Frist Center', 'id': 'FristCenter'}
    return [friend, frist]

# Returns a list of locations with attached queues.
def get_queues():
    q = get_whole_queue()
    locations = get_locations()
    for loc in locations:
      loc['queue'] = [entry for entry in q if entry['location'] == loc['name']]
      loc['num_tas'] = get_active_tas(loc['name'])
      print loc['name'], loc['num_tas']
    return locations

def get_json_queues():
    qs = get_queues()
    return json.dumps(qs)

def get_whole_queue():
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
        tmp['location'] = e.location
        queue.append(tmp)
    return queue

class GetQueue(webapp2.RequestHandler):
    # returns the current queue as a JSON object
    # returns it on the requester's channel, NOT in response
    # assume the channel was already created
    def get(self):
        user = users.get_current_user()
        json_queue = get_json_queues()
        channel.send_message(user.email(), json_queue)

class AddToQueue(webapp2.RequestHandler):
    def post(self):
        print 'In QueueManager.AddToQueue'
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
        hr.location = self.request.get('location')
        print hr.location
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
        hr.helped_datetime = datetime.utcnow()
        hr.attending_ta = user.email()
        hr.put()
        update_active_tas(user.email(), hr.location)
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

        if is_ta(user.email()):
            update_active_tas(user.email(), hr.location)

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
