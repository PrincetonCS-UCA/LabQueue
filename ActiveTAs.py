from google.appengine.api import memcache
from datetime import datetime, timedelta

ACTIVE_TAS_KEY = 'tas'
MAX_INACTIVITY_TIME = timedelta(minutes=45)
DEFAULT_ACTIVE = 2  # If the cache is empty for whatever reason, guess there are 2 active TAs

# Our best guess at how many TAs are in the lab right now
def get_num_active():
    client = memcache.Client()
    d = client.get(ACTIVE_TAS_KEY)
    if d is None:
        client.set(ACTIVE_TAS_KEY, {})
        return DEFAULT_ACTIVE
    return len(d)

# Whenever a TA does something, update their active status
def update_active_tas(ta):
    client = memcache.Client()
    if client.get(ACTIVE_TAS_KEY) is None:
        client.add(ACTIVE_TAS_KEY, {})
    while True:
        d = client.gets(ACTIVE_TAS_KEY)
        now = datetime.utcnow()
        d[ta] = now
        to_remove = []
        for k,v in d.iteritems():
            if now - v > MAX_INACTIVITY_TIME:
                to_remove.append(k)
        for k in to_remove:
            del d[k]
        if client.cas(ACTIVE_TAS_KEY, d):
            break

