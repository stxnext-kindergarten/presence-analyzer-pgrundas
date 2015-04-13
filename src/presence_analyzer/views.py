# -*- coding: utf-8 -*-
"""
Defines views.
"""

import calendar
import locale
import logging
from collections import OrderedDict
from operator import itemgetter

from flask import abort, redirect, request
from flask.ext.mako import render_template
from mako.exceptions import TopLevelLookupException

from presence_analyzer.main import app
from presence_analyzer.utils import (
    get_data,
    group_by_weekday,
    get_users_from_xml,
    group_start_end_by_weekday,
    jsonify,
    mean,
    sum_intervals
)

log = logging.getLogger(__name__)  # pylint: disable=invalid-name
locale.setlocale(locale.LC_COLLATE, '')


@app.route('/')
def mainpage():
    """
    Redirects to front page.
    """
    return redirect('/presence_weekday.html')


@app.route('/<string:template>', methods=['GET'])
def template_renderer(template):
    """
    Serves page template if exists
    """
    context = {}
    context['pages'] = OrderedDict()
    context['pages']['presence_weekday'] = 'Presence by weekday'
    context['pages']['mean_time_weekday'] = 'Presence mean time'
    context['pages']['presence_start_end'] = 'Presence start-end'
    context['pages']['weekly_mean_presence'] = 'Weekly presence'
    context['current_page'] = request.path.split('.')[0][1:]
    try:
        return render_template(template, args=context)
    except TopLevelLookupException:
        abort(404)


@app.route('/api/v1/users', methods=['GET'])
@jsonify
def users_view():
    """
    Users listing for dropdown.
    """
    data = get_users_from_xml()
    users = [
        {
            'user_id': user_id,
            'name': data[user_id]['name'],
            'avatar': data[user_id]['avatar']
        }
        for user_id in data
    ]
    return sorted(users, cmp=locale.strcoll, key=itemgetter('name'))


@app.route('/api/v1/mean_time_weekday/<int:user_id>', methods=['GET'])
@jsonify
def mean_time_weekday_view(user_id):
    """
    Returns mean presence time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        return {
            'message': 'User {} not found!'.format(user_id),
            'status': 404
        }

    weekdays = group_by_weekday(data[user_id])
    return [
        (calendar.day_abbr[weekday], mean(intervals))
        for weekday, intervals in enumerate(weekdays)
    ]


@app.route('/api/v1/presence_weekday/<int:user_id>', methods=['GET'])
@jsonify
def presence_weekday_view(user_id):
    """
    Returns total presence time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        return {
            'message': 'User {} not found!'.format(user_id),
            'status': 404
        }

    weekdays = group_by_weekday(data[user_id])
    result = [
        (calendar.day_abbr[weekday], sum(intervals))
        for weekday, intervals in enumerate(weekdays)
    ]
    result.insert(0, ('Weekday', 'Presence (s)'))
    return result


@app.route('/api/v1/presence_start_end/<int:user_id>', methods=['GET'])
@jsonify
def presence_start_end_view(user_id):
    """
    Returns mean presence time in the office of a given user.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        return {
            'message': 'User {} not found!'.format(user_id),
            'status': 404
        }

    weekdays = group_start_end_by_weekday(data[user_id])
    return [
        (
            calendar.day_abbr[weekday],
            mean(intervals['start']),
            mean(intervals['end'])
        )
        for weekday, intervals in enumerate(weekdays)
    ]


@app.route('/api/v1/weekly_mean_presence/<int:user_id>', methods=['GET'])
@jsonify
def weekly_mean_presence_view(user_id):
    """
    Returns mean
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        return {
            'message': 'User {} not found!'.format(user_id),
            'status': 404
        }

    weekdays = group_by_weekday(data[user_id])
    worked_hours, off_hours = sum_intervals([mean(day) for day in weekdays])
    return [
        ['Activity', 'Total hours'],
        ['Worked hours', worked_hours],
        ['Off hours', off_hours],
    ]
