import os
import logging
from datetime import datetime, timedelta

import webapp2
import jinja2
from google.appengine.api import users, channel
from google.appengine.ext import ndb

import QueueManager, ChannelManager, LabTA

import ConfigDefaults
import LabTAUtils
from LabTA import is_ta

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'])

class MainPage(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        json_queue = QueueManager.get_json_queue()
        token = channel.create_channel(user.email())
        if is_ta(user.email()):
            logging.info("{} is a TA".format(user.email()))
        template_values = {'logout_url': users.create_logout_url('/'),
                           'is_ta': is_ta(user.email()),
                           'curr_user': user.email(),
                           'token': token,
                           'queue': json_queue}
        template = JINJA_ENVIRONMENT.get_template('templates/HelpQueue.html')
        self.response.write(template.render(template_values))

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/queue', QueueManager.GetQueue),
    ('/add', QueueManager.AddToQueue),
    ('/mark-helped', QueueManager.MarkAsHelped),
    ('/cancel', QueueManager.CancelFromQueue),
    ('/ta-facebook', LabTA.TAFacebook),
    ('/_ah/channel/connected/', ChannelManager.SubscriberConnect),
    ('/_ah/channel/disconnected/', ChannelManager.SubscriberDisconnect),
    ('/_update-tas', LabTAUtils.SetTAsInNDB)
   # ('/_update-schema', LabTAUtils.InQueueSchemaUpdate)
], debug=True)



