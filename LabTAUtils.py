from google.appengine.ext import ndb
import webapp2

from HelpRequest import HelpRequest, help_queue_key
import logging

# DB update function meant to be run once to update the DB such that
# all entities have the in_queue computed property.
# Also make sure they're all in the same ancestor group.
class InQueueSchemaUpdate(webapp2.RequestHandler):
    def get(self):
        q = HelpRequest.query()
        q.fetch()
        x = 0
        for e in q:
            x = x + 1
            if x % 100 == 0:
                logging.info("Num Complete: {}".format(x))
            e.put_async()
        self.response.write("Update Complete.")
