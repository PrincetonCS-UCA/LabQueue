from google.appengine.ext import ndb

HELP_QUEUE_NAME = 'default_queue'

def help_queue_key(help__queue_name=HELP_QUEUE_NAME):
    return ndb.Key('HelpQueue', help__queue_name)

class HelpRequest(ndb.Model):
    name = ndb.StringProperty()
    netid = ndb.StringProperty()
    help_msg = ndb.TextProperty()
    been_helped = ndb.BooleanProperty(default=False)
    canceled = ndb.BooleanProperty(default=False)
    in_queue = ndb.ComputedProperty(lambda self: (not self.been_helped and not self.canceled))
    request_datetime = ndb.DateTimeProperty(auto_now_add=True)
    attending_ta = ndb.StringProperty()
    helped_datetime = ndb.DateTimeProperty()
    course = ndb.StringProperty()
    location = ndb.StringProperty()

    @property
    def wait_time(self):
        return None if self.helped_datetime is None else (self.helped_datetime - self.request_datetime)


