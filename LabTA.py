from google.appengine.ext import ndb
import webapp2
import logging
import jinja2
import os
from google.appengine.api import memcache
from datetime import datetime, timedelta

ACTIVE_TAS_KEY = 'tas'
MAX_INACTIVITY_TIME = timedelta(minutes=45)
DEFAULT_ACTIVE = 2  # If the cache is empty for whatever reason, guess there are 2 active TAs
LABTA_GROUP_NAME = 'default_tas'
IMAGE_DIRECTORY = 'img/TAs'
ROW_LENGTH = 3
JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'])

# Refreshes the memcached active TA object.
# If passed in a TA, it adds/updates that TA.
# If no parameter or None is given, it will only refresh.
# Returns the number of TAs we believe are active.
def update_active_tas(ta=None, location=None):
    client = memcache.Client()
    if client.get(ACTIVE_TAS_KEY) is None:
        client.add(ACTIVE_TAS_KEY, {})
    while True:
        d = client.gets(ACTIVE_TAS_KEY)
        now = datetime.utcnow()
        if ta is not None:
            d[ta] = {'time':now, 'location':location}
        to_remove = []
        for k,v in d.iteritems():
            if now - v['time'] > MAX_INACTIVITY_TIME:
                to_remove.append(k)
        for k in to_remove:
            del d[k]
        if client.cas(ACTIVE_TAS_KEY, d):
            break
    return len(d)

def get_active_tas(location=None):
    if location is None:
        print 'none location'
        return 0
    client = memcache.Client()
    if (client.get(ACTIVE_TAS_KEY) is None):
        client.add(ACTIVE_TAS_KEY, {})
    d = client.gets(ACTIVE_TAS_KEY)

    count = 0
    for k,v in d.iteritems():
        print v
        if v['location'] == location:
            count += 1
    return count

def labta_key(labta_group_name=LABTA_GROUP_NAME):
    return ndb.Key('LabTA', labta_group_name)

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
        self.response.write(template.render({'tas': active_tas,
                                             'ROW_LENGTH': ROW_LENGTH}))

class AcknowledgeModal(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('templates/Acknowledge.html')
        self.response.write(template.render({'name': self.request.GET['name'],
                                             'img_path': self.request.GET['img']}))

