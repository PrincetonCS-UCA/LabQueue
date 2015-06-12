import logging
from datetime import datetime, timedelta
import webapp2
from google.appengine.api import channel, users, memcache
from google.appengine.ext import ndb

from google.net.proto.ProtocolBuffer import ProtocolBufferDecodeError

from HelpRequest import HelpRequest, help_queue_key
from LabTA import LabTA, labta_key, is_ta, update_active_tas
import json
import ChannelManager

import cgi   # cgi.escape to sanitize submitted fields

def get_json_queue():
    q = HelpRequest.query(ancestor=help_queue_key())
    q = q.filter(HelpRequest.been_helped == False)
    q = q.filter(HelpRequest.canceled == False)
    q = q.order(HelpRequest.request_datetime)
    q.fetch()
    queue = []
    for e in q:
        current = {}
        # escape all strings before they are sent to JSON
        # to prevent XSS
        current['name'] = cgi.escape(e.name, True)
        current['email'] = cgi.escape(e.netid, True)
        current['help_msg'] = cgi.escape(e.help_msg, True)
        current['course'] = cgi.escape(e.course, True)
        current['id'] = e.key.id()
        current['full_id'] = e.key.urlsafe()
        queue.append(current)
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

def fetch_help_request(requester = None, full_id = None):
    """This method fetches the HelpRequest object from database that
    corresponds to the one that is to be processed by a call (currently
    'cancel' or 'mark_help'). Two ways of obtaining such an object is
    either by giving the requester's netid - in theory a given requester
    can only have one live query at a time - or by given the pickled
    primary key of the row in question."""
    
    hr = None
    
    # Best solution: get HelpRequest from pickled database key
    if full_id:
        try:
            key = ndb.Key(urlsafe = full_id)
            hr = key.get()
        except ProtocolBufferDecodeError:
            # This happens if the full_id is garbage (as even if the
            # full_id corresponds to a key that no longer exists it should
            # be unpickled correctly - in this case the key.get() will
            # simply return None).
            
            logging.error(
              "Could not recover HelpRequest from bad id {}".format(full_id))
        
        if hr:
            return hr
          
        logging.error("Failed HelpRequest access from id {}".format(full_id))

    # Fallback: get HelpRequest by querying for open requests by a user
    if requester:
        q = HelpRequest.query(HelpRequest.in_queue == True,
                              HelpRequest.netid == requester,
                              ancestor=help_queue_key())

        # NOTE: Not sure this is very helpful...
        if q.count() != 1:
            logging.error("Database corrupt for requester {}".format(requester))
            return
        
        hr = q.get()
        return hr
      
      
              
class MarkAsHelped(webapp2.RequestHandler):
    def post(self):
        user = users.get_current_user()
        hr = fetch_help_request(requester = self.request.get('email'),
                                full_id   = self.request.get('full_id'))
        if hr:
            update_active_tas(user.email())
            hr.been_helped = True
            hr.helped_datetime = datetime.utcnow()
            hr.attending_ta = user.email()
            hr.put()
            ChannelManager.queue_update()
            ta = LabTA.query(LabTA.email == hr.attending_ta,
                             ancestor=labta_key()).fetch()[0]
            ChannelManager.notify_request_accepted(hr.netid,
                                                   ta.first_name,
                                                   ta.img_path)

class CancelFromQueue(webapp2.RequestHandler):
    def post(self):
        user = users.get_current_user()
        hr = fetch_help_request(requester = self.request.get('email'),
                                full_id   = self.request.get('full_id'))
        if hr:
           hr.canceled = True
           
           if is_ta(user.email()):
               update_active_tas(user.email())
               
               # Update this field if the cancellation comes from the TA
               # and the TA isn't the originator of the request
               #
               # FIXME: there should be a field dedicated to the canceller.
               
               if hr.netid != user.email():
                   hr.attending_ta = user.email()
                 
           hr.put()
           ChannelManager.queue_update()

           
class ClearQueue(webapp2.RequestHandler):
    @ndb.toplevel
    def post(self):
        user = users.get_current_user()

        # NOTE: previously this command could be run by anybody; now it
        # is restricted to TAs; consider restricting this further.
        
        if is_ta(user.email()):
          logging.info("User {} cleared the queue".format(user.email()))
          q = HelpRequest.query(HelpRequest.in_queue == True,
                                ancestor=help_queue_key()).fetch()
          for hr in q:
              hr.canceled = True

              # NOTE: same as above, if cancelled by TA, mark it.
              if hr.netid != user.email():
                   hr.attending_ta = user.email()
              
              hr.put()
          ChannelManager.queue_update()
