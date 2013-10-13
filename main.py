import os
import logging
import datetime

import webapp2
import jinja2
from google.appengine.api import users
from google.appengine.ext import ndb

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'])

HELP_QUEUE_NAME = 'default_queue'

LAB_TAS = ['daifotis@princeton.edu', 'alex.daifotis@gmail.com', 'mcspedon@princeton.edu', 'siderius@princeton.edu',
           'auttamad@princeton.edu', 'gowen@princeton.edu', 'psyu@princeton.edu', 'codyw@princeton.edu', 'eportnoy@princeton.edu',
           'usikder@princeton.edu', 'knv@princeton.edu', 'aabdelaz@princeton.edu', 'aksimpso@princeton.edu',
           'mmcgil@princeton.edu', 'bspar@princeton.edu']

def help_queue_key(help__queue_name=HELP_QUEUE_NAME):
    return ndb.Key('HelpQueue', help__queue_name)

class HelpRequest(ndb.Model):
    name = ndb.StringProperty()
    netid = ndb.StringProperty()
    help_msg = ndb.StringProperty()
    been_helped = ndb.BooleanProperty(default=False)
    canceled = ndb.BooleanProperty(default=False)
    request_datetime = ndb.DateTimeProperty(auto_now_add=True)
    attending_ta = ndb.StringProperty()

class HelpQueue(webapp2.RequestHandler):
    # enforce user login
    def get(self):
        user = users.get_current_user()

        help_query = HelpRequest.query(HelpRequest.been_helped == False, HelpRequest.canceled == False,
                                       ancestor=help_queue_key()).order(HelpRequest.request_datetime)
        help_reqs = help_query.fetch()
        template_values = {'help_requests': help_reqs,
                           'logout_url': users.create_logout_url('/'),
                           'is_ta': user.email() in LAB_TAS,
                           'curr_user': user.email()}
        template = JINJA_ENVIRONMENT.get_template('templates/HelpQueue.html')

        self.response.write(template.render(template_values))

    #enforce user login
    def post(self):
        user = users.get_current_user()
        if self.request.get('action') == 'help':
            req_query = HelpRequest.query(HelpRequest.netid == self.request.get('netid'),
                                          HelpRequest.been_helped == False)
            reqs = req_query.fetch(1)
            for r in reqs:
                r.been_helped = True
                r.attending_ta = user.email()
                r.put()
        elif self.request.get('action') == 'cancel':
            req_query = HelpRequest.query(HelpRequest.netid == self.request.get('netid'),
                                          HelpRequest.canceled == False)
            reqs = req_query.fetch(1)
            for r in reqs:
                r.canceled = True
                r.put()
        elif self.request.get('action') == 'enter_queue':
            help_queue = HelpRequest(parent=help_queue_key())
            help_queue.name = self.request.get('name')
            help_queue.netid = user.email()
            help_queue.help_msg = self.request.get('help_msg')

            q = HelpRequest.query(HelpRequest.netid == help_queue.netid,
                                  HelpRequest.been_helped == False,
                                  HelpRequest.canceled == False)
            # TODO: Error to user if they try to double enter queue
            if q.count() == 0:
                help_queue.put()
        self.redirect('/')

app = webapp2.WSGIApplication([
    ('/', HelpQueue)
], debug=True)



