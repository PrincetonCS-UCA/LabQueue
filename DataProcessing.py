from google.appengine.ext.remote_api import remote_api_stub
from main import HelpRequest, help_queue_key

import getpass
import numpy


def auth_func():
    return (raw_input('Email:'), getpass.getpass('Password:'))

remote_api_stub.ConfigureRemoteApi(None, '/_ah/remote_api', auth_func,
                                    'golden-cove-356.appspot.com')

# Pulls all latest data from the datastore so that we have it
# locally for processing. Returns a 2-tuple of lists, 1 list being
# all requests, the second being just the ones where help was given.
def pull_data(outfile_name='output.csv'):
    query = HelpRequest.query().order(HelpRequest.request_datetime)
    res = query.fetch()
    only_helped = [x for x in res if x.been_helped == True]
    return (res, only_helped)

def class_dist(all_reqs, helped):
    print 'PROCESSING CLASS DISTRIBUTION'
    print 'TOTAL RECORDS: {}'.format(len(all_reqs))
    print 'TOTAL HELPED: {}'.format(len(helped))
    
    reqs_109 = [x for x in helped if x.course == 'COS 109']
    reqs_126 = [x for x in helped if x.course == 'COS 126']
    reqs_226 = [x for x in helped if x.course == 'COS 226']
    reqs_217 = [x for x in helped if x.course == 'COS 217']   
    print 'PERCENT 109: {:.1f}%'.format(len(reqs_109) / float(len(helped)) * 100)
    print 'PERCENT 126: {:.1f}%'.format(len(reqs_126) / float(len(helped)) * 100)
    print 'PERCENT 226: {:.1f}%'.format(len(reqs_226) / float(len(helped)) * 100)
    print 'PERCENT 217: {:.1f}%'.format(len(reqs_217) / float(len(helped)) * 100)
    print

def day_dist(reqs):
    day_map = dict()
    for req in reqs:
        if req.helped_datetime == None: continue
        if req.helped_datetime.weekday() in day_map:
            day_map[req.helped_datetime.weekday()] += 1
        else:
            day_map[req.helped_datetime.weekday()] = 1
    print 'PERCENT SUNDAY: {:.1f}%'.format(day_map[6] / float(len(reqs)) * 100.0)
    print 'PERCENT MONDAY: {:.1f}%'.format(day_map[0] / float(len(reqs)) * 100.0)
    print 'PERCENT TUESDAY: {:.1f}%'.format(day_map[1] / float(len(reqs)) * 100.0)
    print 'PERCENT WEDNESDAY: {:.1f}%'.format(day_map[2] / float(len(reqs)) * 100.0)
    print 'PERCENT THURSDAY: {:.1f}%'.format(day_map[3] / float(len(reqs)) * 100.0)
    print 'PERCENT FRIDAY: {:.1f}%'.format(day_map[4] / float(len(reqs)) * 100.0)
    print 'PERCENT SATURDAY: {:.1f}%'.format(day_map[5] / float(len(reqs)) * 100.0)
    print

def ta_freqs(reqs):
    ta_map = dict()
    for req in reqs:
        if req.attending_ta in ta_map:
            ta_map[req.attending_ta] += 1
        else:
            ta_map[req.attending_ta] = 1
    
    print 'TOP 5 TAs BY VOLUME:'
    sorted_tas = sorted(ta_map.items(), key=lambda x: x[1], reverse=True)
    for elem in sorted_tas[0:5]:
        print '{0} : {1}'.format(elem[0], elem[1])
    print 'BOTTOM 5 TAs BY VOLUME:'
    for elem in sorted_tas[-5:len(sorted_tas)]:
        print '{0} : {1}'.format(elem[0], elem[1])
    vals = [x[1] for x in sorted_tas]
    print 'AVERAGE REQUESTS PER TA: {:.2f}'.format(numpy.mean(vals))
    print 'STDDEV: {:.2f}'.format(numpy.std(vals))

def main():
    print 'here'
    (all_reqs, helped) = pull_data()
    class_dist(all_reqs, helped)
    day_dist(helped)
    ta_freqs(helped)
    print 'Done.'

if __name__ == '__main__':
    main()

