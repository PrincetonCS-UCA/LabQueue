# File sets up constants and other config

from google.appengine.api import lib_config

TA_EMAILS = set()
for line in open('ta_emails.txt', 'r'):
    TA_EMAILS.add(line.strip().lower())

_config = lib_config.register('ConfigDefaults', {'TA_EMAILS': TA_EMAILS})