# -*- coding: utf-8 -*-
"""
Helper functions used in views.
"""

import csv
import hashlib
import logging
import threading
import time
from datetime import datetime, timedelta
from functools import wraps
from json import dumps

from flask import Response
from lxml import etree

from presence_analyzer.main import app

log = logging.getLogger(__name__)  # pylint: disable=invalid-name

CACHE = {}


def lock(function):
    """
    Decorator for preventing using a function at the same time.
    """
    @wraps(function)
    def inner(*args, **kwargs):  # pylint: disable=missing-docstring
        with threading.Lock():
            return function(*args, **kwargs)
    return inner


def cache(duration):
    """
    Decorator for caching the result of a function.
    """
    def decorator(function):  # pylint: disable=missing-docstring
        @wraps(function)
        def inner(*args, **kwargs):  # pylint: disable=missing-docstring
            key = hashlib.sha1(function.__name__).hexdigest()
            current_time = int(time.time() * 1000)
            if key in CACHE and current_time - CACHE[key]['time'] < duration:
                return CACHE[key]['data']

            result = function(*args, **kwargs)
            CACHE[key] = {
                'data': result,
                'time': current_time
            }
            return result
        return inner
    return decorator


def jsonify(function):
    """
    Creates a response with the JSON representation of wrapped function result.
    """
    @wraps(function)
    def inner(*args, **kwargs):
        """
        This docstring will be overridden by @wraps decorator.
        """
        return Response(
            dumps(function(*args, **kwargs)),
            mimetype='application/json'
        )
    return inner


def get_users_from_xml():
    """
    Extracts user informations from user.xml and groups it by user_id.

    Example structure:
    users = {
        '151': {
            'avatar': '/api/images/users/151',
            'name': 'Dawid J.'
        },
        '150': {
            'avatar': '/api/images/users/150',
            'name': u'Kamil G.'
        }
    """
    tree = etree.parse(app.config['USERS_XML'])
    api_url = '{}://{}'.format(
        tree.find('server').find('protocol').text,
        tree.find('server').find('host').text
    )
    result = {}
    for user in tree.find('users'):
        result[int(user.get('id'))] = {
            'name': unicode(user.find('name').text),
            'avatar': '{}{}'.format(api_url, user.find('avatar').text)
        }
    return result


@lock
@cache(600)
def get_data():
    """
    Extracts presence data from CSV file and groups it by user_id.

    It creates structure like this:
    data = {
        'user_id': {
            datetime.date(2013, 10, 1): {
                'start': datetime.time(9, 0, 0),
                'end': datetime.time(17, 30, 0),
            },
            datetime.date(2013, 10, 2): {
                'start': datetime.time(8, 30, 0),
                'end': datetime.time(16, 45, 0),
            },
        }
    }
    """
    data = {}
    with open(app.config['DATA_CSV'], 'r') as csvfile:
        presence_reader = csv.reader(csvfile, delimiter=',')
        for i, row in enumerate(presence_reader):
            if len(row) != 4:
                # ignore header and footer lines
                continue

            try:
                user_id = int(row[0])
                date = datetime.strptime(row[1], '%Y-%m-%d').date()
                start = datetime.strptime(row[2], '%H:%M:%S').time()
                end = datetime.strptime(row[3], '%H:%M:%S').time()
            except (ValueError, TypeError):
                log.debug('Problem with line %d: ', i, exc_info=True)

            data.setdefault(user_id, {})[date] = {'start': start, 'end': end}

    return data


def group_by_weekday(items):
    """
    Groups presence entries by weekday.
    """
    result = [[], [], [], [], [], [], []]  # one list for every day in week
    for date in items:
        start = items[date]['start']
        end = items[date]['end']
        result[date.weekday()].append(interval(start, end))
    return result


def group_start_end_by_weekday(items):
    """
    Groups presence entrences/leaves grouped by weekday.
    """
    result = [{'start': [], 'end': []} for _ in xrange(7)]

    for date in items:
        start = items[date]['start']
        end = items[date]['end']
        result[date.weekday()]['start'].append(seconds_since_midnight(start))
        result[date.weekday()]['end'].append(seconds_since_midnight(end))

    return result


def sum_timedelta(interval):  # pylint: disable=redefined-outer-name
    """
    Sums timedelta time and returns float in HH.MM.
    """
    hours, remainder = divmod(interval.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    hours = hours + (interval.days * 24)
    return float('{}.{}'.format(hours, minutes))


def sum_intervals(items):
    """
    Sums weekday intervals and returns tuple with the sum of worked hours and
    off time hours.
    """
    worked_interval = timedelta()
    whole_week = timedelta(hours=168)

    for interval in items:  # pylint: disable=redefined-outer-name
        worked_interval += timedelta(seconds=(interval))

    off_interval = whole_week - worked_interval

    return sum_timedelta(worked_interval), sum_timedelta(off_interval)


def seconds_since_midnight(time):  # pylint: disable=redefined-outer-name
    """
    Calculates amount of seconds since midnight.
    """
    return time.hour * 3600 + time.minute * 60 + time.second


def interval(start, end):
    """
    Calculates inverval in seconds between two datetime.time objects.
    """
    return seconds_since_midnight(end) - seconds_since_midnight(start)


def mean(items):
    """
    Calculates arithmetic mean. Returns zero for empty lists.
    """
    return float(sum(items)) / len(items) if len(items) > 0 else 0
