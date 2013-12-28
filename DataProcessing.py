import csv
from csv import DictReader, DictWriter
import numpy
from sys import argv, stdout
from datetime import datetime, timedelta, time
from copy import deepcopy
import hashlib
from random import random
import matplotlib.pyplot as plt

## First argument is the input filename in csv format,
## the first row should be a column header.

ISO_FORMAT = '%Y-%m-%dT%H:%M:%S'
DAYS = ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY', 'SUNDAY']
ENTER = 0
LEAVE = 1

# Just return a list of all of the records
# Use dict reader, so each records is a dict with all the fields
def load_data_into_mem(fname):
    dr = DictReader(open(fname, 'r'))
    def utc_to_est(x):
        delt = timedelta(hours=5) # EST offset -0500 from UTC
        req_dt = datetime.strptime(x['request_datetime'], ISO_FORMAT)
        x['request_datetime'] = req_dt - delt
        if x['helped_datetime'] != '':
            h_dt = datetime.strptime(x['helped_datetime'], ISO_FORMAT)
            x['helped_datetime'] = h_dt - delt
        else:
            x['helped_datetime'] = None
        return x
    return map(utc_to_est, dr)

def write_anonymized_data(ofname, records):
    cpy = deepcopy(records)
    salt = str(random())
    dw = DictWriter(open(ofname, 'w'), cpy[0].keys())
    dw.writeheader()
    for r in cpy:
        sha256 = hashlib.new('sha256')
        sha256.update(salt)
        sha256.update(r['netid'])
        r['netid'] = sha256.hexdigest()
        sha256 = hashlib.new('sha256')
        sha256.update(salt)
        sha256.update(r['name'])
        r['name'] = sha256.hexdigest()
        dw.writerow(r)

def general_stats(all_reqs, helped):
    all_reqs.sort(key=lambda x: x['request_datetime'])
    print 'FIRST REQUEST AT: {}'.format(all_reqs[0]['request_datetime'])
    print 'LAST REQUEST AT: {}'.format(all_reqs[-1]['request_datetime'])
    total = len(all_reqs)
    print 'TOTAL RECORDS: {}'.format(total)
    count_accepted = len(helped)
    print 'NUMBER ACKNOWLEDGED: {}'.format(count_accepted)
    print 'PERCENT TA HELPED: {:.1f}%'.format(float(count_accepted) / total * 100.0)
    count_canceled = total - count_accepted
    print 'PERCENT CANCELED: {:.1f}%'.format(float(count_canceled) / total * 100.0)
    print

def class_dist(helped):
    print 'PROCESSING CLASS DISTRIBUTION'
    reqs_109 = [x for x in helped if x['course'] == 'COS 109']
    reqs_126 = [x for x in helped if x['course'] == 'COS 126']
    reqs_226 = [x for x in helped if x['course'] == 'COS 226']
    reqs_217 = [x for x in helped if x['course'] == 'COS 217']
    print 'PERCENT 109: {:.1f}%'.format(len(reqs_109) / float(len(helped)) * 100)
    print 'PERCENT 126: {:.1f}%'.format(len(reqs_126) / float(len(helped)) * 100)
    print 'PERCENT 226: {:.1f}%'.format(len(reqs_226) / float(len(helped)) * 100)
    print 'PERCENT 217: {:.1f}%'.format(len(reqs_217) / float(len(helped)) * 100)
    print

def request_distribution(reqs):
    print 'PROCESSING DISTRIBUTION BY DAY AND CLASS'
    def class_dict():
        return {'COS 109': 0, 'COS 126': 0, 'COS 226': 0, 'COS 217': 0}
    day_map = dict({0: class_dict(), 1: class_dict(), 2: class_dict(), 3: class_dict(),
                    4: class_dict(), 5: class_dict(), 6: class_dict()})

    for req in reqs:
        dt = req['request_datetime']
        day_map[dt.weekday()][req['course']] += 1
    print 'BY DAY SUMMARY'
    for day, cdict in sorted(day_map.items(), key=lambda x: x[0]):
        print 'PERCENT {}: {:.1f}%'.format(DAYS[day], numpy.sum(cdict.values()) / float(len(reqs)) * 100.0)
    print 'RAW DATA...'
    for day, cdict in sorted(day_map.items(), key=lambda x: x[0]):
        stdout.write('{}\n\tCOS 109: {}\n\tCOS 126: {}\n\tCOS 226: {}\n\tCOS 217: {}\n'.format(
            DAYS[day], cdict['COS 109'], cdict['COS 126'], cdict['COS 226'], cdict['COS 217']))
    print

def ta_freqs(reqs):
    print 'PROCESSING INDIVIDUAL TA THROUGHPUT'
    ta_map = dict()
    for req in reqs:
        if req['attending_ta'] in ta_map:
            ta_map[req['attending_ta']] += 1
        else:
            ta_map[req['attending_ta']] = 1
    
    print 'TOTAL TAs: {}'.format(len(ta_map.keys()))
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
    print 'TOP 5 TAs AS PERCENT OF VOLUME: {:.1f}%'.format(numpy.sum(vals[:4]) / float((len(reqs))) * 100.0)

    ta_fname = 'ta_cdf.csv'
    print 'OUTPUTTING TA WORK CDF TO {}'.format(ta_fname)
    ta_writer = csv.writer(open(ta_fname, 'w'))
    ta_writer.writerow(['NumTAs', 'PercentRequestFilled'])
    sum = 0.0
    for idx, val in enumerate(sorted_tas, start=1):
        sum += val[1]
        ta_writer.writerow([idx, sum/len(reqs)])
    print

def student_freqs(reqs):
    print 'PROCESSING INDIVIDUAL STUDENT USAGE'
    stud_map = dict()
    for r in reqs:
        if r['netid'] in stud_map:
            stud_map[r['netid']] += 1
        else:
            stud_map[r['netid']] = 1
    print 'TOTAL UNIQUE STUDENTS: {}'.format(len(stud_map.keys()))
    sorted_studs = sorted(stud_map.items(), key=lambda x: x[1], reverse=True)
    print 'TOP 20 STUDENTS BY VOLUME:'
    for e in sorted_studs[:20]:
        print '{} : {}'.format(e[0], e[1])
    vals = [x[1] for x in sorted_studs]
    print 'AVERAGE REQUESTS PER STUDENT: {:.2f}'.format(numpy.mean(vals))
    print 'STDEV: {:.2f}'.format(numpy.std(vals))

    stud_fname = 'stud_cdf.csv'
    print 'OUTPUTTING STUDENT REQUEST CDF TO {}'.format(stud_fname)
    stud_writer = csv.writer(open(stud_fname, 'w'))
    stud_writer.writerow(['NumStudents', 'PercentRequests'])
    sum = 0.0
    for idx, val in enumerate(sorted_studs, start=1):
        sum += val[1]
        stud_writer.writerow([idx, sum/len(reqs)])
    print

def wait_times(reqs):
    init_sz = len(reqs)
    print 'INITIAL DATA SET SIZE: {}'.format(init_sz)
    # Remove entries where due to error during re-write, we didn't record request ack time
    reqs = filter(lambda x: x['helped_datetime'] != None, reqs)
    # Also remove outlier entries that were likely the result of human error
    # Generously allow for 2hr max wait time
    delts = [((x['helped_datetime'] - x['request_datetime']).total_seconds() / 60.0, x['request_datetime']) for x in reqs]
    delts = filter(lambda x: x[0] < 120.0, delts)
    print 'SIZE AFTER DATA ERRORS REMOVED: {}'.format(len(delts))
    print 'AVERAGE WAIT TIME: {:.2f} minutes'.format(numpy.mean([x[0] for x in delts]))
    print 'STDEV: {:.2f} minutes'.format(numpy.std([x[0] for x in delts]))
    print 'SHOWING BREAKDOWN BY DAY OF WEEK'
    for d in range(0, 7):
        tmp = filter(lambda x: x[1].weekday() == d, delts)
        print 'AVERAGE WAIT ON {}: {:.2f}'.format(DAYS[d], numpy.mean([x[0] for x in tmp]))
    print 'SHOWING BREAKDOWN BY TIME'
    # Hours 7-11pm
    for i in range(19, 23):
        t1 = time(hour=i)
        t2 = time(hour=i+1)
        tmp = filter(lambda x: x[1].time() >= t1 and x[1].time() < t2, delts)
        print 'AVERAGE WAIT TIME BETWEEN {} AND {}: {:.2f}'.format(t1.isoformat(), t2.isoformat(),
                                                                   numpy.mean([x[0] for x in tmp]))
    plt.hist([x[0] for x in delts])
    plt.show()
    # We want to show that requests are mostly answered in a short period of time
    # Output data needed for chart where X -- Time Waited Y -- Percent of Requests
    # Point being, majority of requests are answered pretty quickly
    dist_fname = 'wait_dist.csv'
    print 'OUTPUTTING WAIT TIME DIST TO {}'.format(dist_fname)
    dist_writer = csv.writer(open(dist_fname, 'w'))
    dist_writer.writerow(['TimeWaited', 'PercentRequestFilled'])
    delts.sort(key=lambda x: x[0])
    for idx, val in enumerate(delts, start=1):
        dist_writer.writerow([val[0], float(idx)/len(delts)])
    print

# Analyze how long it took the TAs to respond to individual requests.
# We need to impute this from the data since we explicitly record ticket close times.
# Note this is not really perfect since we didn't record exit times if
# it was a cancel instead of an ack, though this should be insignificant.
def ta_request_times(reqs):
    # Reconstruct queue entry and exit events we will play through
    # Remove entries where due to error during re-write, we didn't record request ack time
    reqs = filter(lambda x: x['helped_datetime'] != None, reqs)
    events = []
    for r in reqs:
        events.append((r['request_datetime'], ENTER, r))
        events.append((r['helped_datetime'], LEAVE, r))
    events.sort(key=lambda x: x[0])

    work_times = []
    queue_len = 0
    ta_flags = set()
    max_min = 45
    for e in events:
        if e[1] == ENTER:
            queue_len += 1
        else:
            r = e[2]
            if r['attending_ta'] in ta_flags:
                delt = (r['helped_datetime'] - r['request_datetime']).total_seconds() / 60.0
                if delt < max_min:
                    work_times.append((delt, r['course'], r['attending_ta']))
            else:
                ta_flags.add(r['attending_ta'])
            queue_len -= 1
            if queue_len == 0:
                ta_flags.clear()

    dist_fname = 'work_dist.csv'
    print 'OUTPUTTING WORK TIME DIST TO {}'.format(dist_fname)
    dist_writer = csv.writer(open(dist_fname, 'w'))
    dist_writer.writerow(['Course', 'TimeSpent'])
    map(lambda x: dist_writer.writerow((x[0], x[1])), work_times)

    dist_writer.writerow(['TimeWaited', 'PercentRequestFilled'])
    print 'NUMBER OF USABLE OBSERVATIONS: {}'.format(len(work_times))
    print 'AVERAGE WORK TIME: {:.2f} MINUTES'.format(numpy.mean([x[0] for x in work_times]))
    print 'STDEV WORK TIME: {:.2f} MINUTES'.format(numpy.std([x[0] for x in work_times]))
    #plt.hist([x[0] for x in work_times])
    #plt.show()
    print 'SHOWING BREAKDOWN BY CLASS'
    c109 = filter(lambda x: x[1] == 'COS 109', work_times)
    print 'AVERAGE WORK TIME ON COS 109 STUDENTS: {:.2f}'.format(numpy.mean([x[0] for x in c109]))
    c126 = filter(lambda x: x[1] == 'COS 126', work_times)
    print 'AVERAGE WORK TIME ON COS 126 STUDENTS: {:.2f}'.format(numpy.mean([x[0] for x in c126]))
    c226 = filter(lambda x: x[1] == 'COS 226', work_times)
    print 'AVERAGE WORK TIME ON COS 226 STUDENTS: {:.2f}'.format(numpy.mean([x[0] for x in c226]))
    c217 = filter(lambda x: x[1] == 'COS 217', work_times)
    print 'AVERAGE WORK TIME ON COS 217 STUDENTS: {:.2f}'.format(numpy.mean([x[0] for x in c217]))


def main():
    help_records = load_data_into_mem(argv[1])
    helped = filter(lambda x: x['been_helped'] == 'True' and x['course'] != '', help_records)
    #write_anonymized_data('anonymized-' + argv[1], help_records)
    general_stats(help_records, helped)
    request_distribution(helped)
    ta_freqs(helped)
    student_freqs(helped)
    wait_times(helped)
    ta_request_times(help_records)
    print 'Done.'

if __name__ == '__main__':
    main()

