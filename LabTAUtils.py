from google.appengine.ext import ndb
import webapp2

from HelpRequest import HelpRequest, help_queue_key
import logging
from LabTA import LabTA, labta_key

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

# Read off current TAs from text file, adds them to DB
# if they are not already in it. Do this whenever new
# TAs are added to the roster
class SetTAsInNDB(webapp2.RequestHandler):
    def get(self):
        active_tas = dict()
        for line in open('tas.dat', 'r'):
            tmp = line.split(',')
            ta = LabTA(parent=labta_key())
            logging.info(line)
            ta.first_name = tmp[0]
            ta.last_name = tmp[1]
            ta.class_year = tmp[2]
            ta.email = tmp[3].strip()
            ta.is_active = True
            active_tas[ta.email] = ta

        # Ones already in the DB
        for t in LabTA.query().fetch():
            if t.email in active_tas:
                tmp = active_tas[t.email]
                t.first_name = tmp.first_name
                t.last_name = tmp.last_name
                t.class_year = tmp.class_year
                t.is_active = True
                del active_tas[t.email]
            else:
                t.is_active = False
            t.put()
        # Add the new TAs
        for t in active_tas.itervalues():
            t.put()
        self.response.write("Update Complete.")
