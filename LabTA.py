from google.appengine.ext import ndb
import webapp2
import logging
import jinja2
import os

LABTA_GROUP_NAME = 'default_tas'
IMAGE_DIRECTORY = 'img/TAs'
ROW_LENGTH = 3

def labta_key(labta_group_name=LABTA_GROUP_NAME):
    return ndb.Key('LabTA', labta_group_name)

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'])

class LabTA(ndb.Model):
    first_name = ndb.StringProperty()
    last_name = ndb.StringProperty()
    email = ndb.StringProperty()
    class_year = ndb.StringProperty()
    is_active = ndb.BooleanProperty()

    @property
    def netid(self):
        return self.email.split('@')[0]

    @property
    def img_path(self):
        return os.path.join(IMAGE_DIRECTORY, self.netid + '.jpg')

def is_ta(email):
    logging.info("Checking {}".format(email))
    logging.info(len(LabTA.query(LabTA.email == email).fetch()))
    return LabTA.query(LabTA.email == email).count() > 0

class TAFacebook(webapp2.RequestHandler):
    def get(self):
        active_tas = LabTA.query(LabTA.is_active == True, ancestor=labta_key()).order(LabTA.class_year)
        # see if we have a picture of the TAs, otherwise mark them as using the default
        template = JINJA_ENVIRONMENT.get_template('templates/Facebook.html')
        self.response.write(template.render({'tas' : active_tas,
                                             'ROW_LENGTH' : ROW_LENGTH}))

class AcknowledgeModal(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('templates/Acknowledge.html')
        self.response.write(template.render({'name': self.request.GET['name'],
                                             'img_path': self.request.GET['img']}))

