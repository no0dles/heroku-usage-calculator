import sys
import re
import datetime

HEROKU_SLEEP_TIMEOUT = 30


def invalid_args():
    print 'usage: python main.py [access log file]'


def extract_date(log):
    m = re.match("(\d+.\d+.\d+.\d+)\s-\s-\s\[(?P<date>(.+))\]\s.+", log)
    if m:
        return parse_date(m.group("date"))
    return None


def parse_date(value):
    return datetime.datetime.strptime(value[:20], "%d/%b/%Y:%H:%M:%S")


def get_minute_diff(date1, date2):
    return (date2-date1).total_seconds()/60


def get_hour_diff(date1, date2):
    return get_minute_diff(date1, date2)/60


def calc_usage(dates):
    dates.sort()

    usages = []
    current_usage = {
        "start": dates[0],
        "end": dates[0] + datetime.timedelta(minutes=HEROKU_SLEEP_TIMEOUT)
    }

    for date in dates:
        minutes = get_minute_diff(current_usage["end"], date)
        if minutes < HEROKU_SLEEP_TIMEOUT:
            current_usage["end"] = date + datetime.timedelta(minutes=HEROKU_SLEEP_TIMEOUT)
        else:
            usages.append(current_usage)
            current_usage = {
                "start": date,
                "end": date + datetime.timedelta(minutes=HEROKU_SLEEP_TIMEOUT)
            }

    return usages


def get_hour_usage(usage):
    return get_hour_diff(usage["start"], usage["end"])


def calc_hour_usage(usages):
    total_usage = 0
    for usage in usages:
        total_usage += get_hour_usage(usage)
    return total_usage


def calc_day_usages(usages):
    day_usages = []
    for i in range(0, len(usages)):
        start = usages[i]["start"]
        end = start + datetime.timedelta(days=1)
        current_usage = 0

        for j in range(i, len(usages)):
            usage = usages[j]
            if usage["start"] <= end:
                if usage["end"] <= end:
                    current_usage += get_hour_usage(usage)
                else:
                    current_usage += get_hour_diff(usage["start"], end)
            else:
                break

        day_usages.append(current_usage)

    return day_usages


def calc_max_hour_usage(usages):
    return max(calc_day_usages(usages))


def calc_min_hour_usage(usages):
    return min(calc_day_usages(usages))


def main():
    if len(sys.argv) != 2:
        invalid_args()
        return

    filename = sys.argv[1]

    try:
        with open(filename, 'r') as f:
            logs = f.readlines()
    except IOError:
        print 'File "%s" not found' % (filename,)
        return

    dates = []
    for log in logs:
        date = extract_date(log)
        if date:
            dates.append(date)

    if len(dates) == 0:
        print 'No log data available'
        return

    usages = calc_usage(dates)
    total_hour_usage = calc_hour_usage(usages)
    total_hours = get_hour_diff(dates[0], dates[-1])
    day_hour_usage = total_hour_usage * (24 / total_hours)
    max_hour_usage = calc_max_hour_usage(usages)
    min_hour_usage = calc_min_hour_usage(usages)

    print "Total usage: %f hours" % (total_hour_usage,)
    print "Max day usage: %f hours" % (max_hour_usage,)
    print "Min day usage: %f hours" % (min_hour_usage,)
    print "Avg day usage: %f hours" % (day_hour_usage,)

main()
