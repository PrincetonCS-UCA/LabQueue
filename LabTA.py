from google.appengine.ext import ndb
import webapp2
import logging


class LabTA(ndb.Model):
    first_name = ndb.StringProperty()
    last_name = ndb.StringProperty()
    email = ndb.StringProperty()
    class_year = ndb.StringProperty()
    is_active = ndb.BooleanProperty()

def is_ta(email):
    logging.info("Checking {}".format(email))
    logging.info(len(LabTA.query(LabTA.email == email).fetch()))
    return LabTA.query(LabTA.email == email).count() > 0

class TAFacebook(webapp2.RequestHandler):
    def get(self):
        pass