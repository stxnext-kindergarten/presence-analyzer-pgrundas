# -*- coding: utf-8 -*-
"""
Presence analyzer unit tests.
"""
from __future__ import unicode_literals

import datetime
import hashlib
import json
import time
import os.path
import unittest
from datetime import timedelta

from presence_analyzer import main, utils

TEST_DATA_CSV = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'test_data.csv'
)
TEST_DATA_XML = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'test_users.xml'
)


# pylint: disable=maybe-no-member, too-many-public-methods
class PresenceAnalyzerViewsTestCase(unittest.TestCase):
    """
    Views tests.
    """

    def setUp(self):
        """
        Before each test, set up a environment.
        """
        main.app.config.update({'DATA_CSV': TEST_DATA_CSV})
        main.app.config.update({'USERS_XML': TEST_DATA_XML})
        self.client = main.app.test_client()

    def tearDown(self):
        """
        Get rid of unused objects after each test.
        """
        pass

    def test_mainpage(self):
        """
        Test main page redirect.
        """
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 302)
        assert resp.headers['Location'].endswith('/presence_weekday.html')
        self.assertEqual(
            resp.headers['Content-Type'], 'text/html; charset=utf-8'
        )

    def test_template_renderer(self):
        """
        Test serving templates
        """
        resp = self.client.get('/presence_weekday.html')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.headers['Content-Type'], 'text/html; charset=utf-8'
        )
        resp = self.client.get('/mean_time_weekday.html')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.headers['Content-Type'], 'text/html; charset=utf-8'
        )
        resp = self.client.get('/fake.html')
        self.assertEqual(resp.status_code, 404)

    def test_api_users(self):
        """
        Test users listing.
        """
        resp = self.client.get('/api/v1/users')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertEqual(len(data), 2)
        user_11 = {
            'user_id': 11,
            'name': 'Maciej D.',
            'avatar': 'https://intranet.stxnext.pl/api/images/users/11'
        }
        user_10 = {
            'user_id': 10,
            'name': 'Maciej Z.',
            'avatar': 'https://intranet.stxnext.pl/api/images/users/10'
        }
        self.assertDictEqual(data[0], user_11)
        self.assertDictEqual(data[1], user_10)
        self.assertListEqual(data, [user_11, user_10])

    def test_mean_time_weekday_view(self):
        """
        Test mean_time_weekday_view view.
        """
        resp = self.client.get('/api/v1/mean_time_weekday/10')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertEqual(len(data), 7)
        self.assertEqual(data[0][1], 0)
        self.assertNotEqual(data[1][1], 0)

        resp = self.client.get('/api/v1/mean_time_weekday/9')
        self.assertEqual(resp.content_type, 'application/json')
        json_data = json.loads(resp.data)
        self.assertDictEqual(json_data, {
            'status': 404,
            'message': 'User 9 not found!'
        })

    def test_presence_weekday_view(self):
        """
        Test presence_weekday_view.
        """
        resp = self.client.get('/api/v1/presence_weekday/10')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertEqual(len(data[0]), 2)
        self.assertEqual(len(data), 8)
        self.assertEqual(data[4], ['Thu', 23705])

        resp = self.client.get('/api/v1/presence_weekday/1')
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(resp.status_code, 200)
        json_data = json.loads(resp.data)
        self.assertDictEqual(json_data, {
            'status': 404,
            'message': 'User 1 not found!'
        })

    def test_presence_start_end_view(self):
        """
        Test presence_start_end_view.
        """
        resp = self.client.get('/api/v1/presence_weekday/2')
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertDictEqual(data, {
            'status': 404,
            'message': 'User 2 not found!'
        })

        resp = self.client.get('/api/v1/presence_start_end/10')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertEqual(len(data[0]), 3)
        self.assertEqual(len(data[1]), 3)
        self.assertEqual(len(data[2]), 3)
        self.assertIn('Tue', data[1])
        self.assertEqual(data[2][1], 33592.0)
        self.assertEqual(data[3][2], 62631.0)

        resp = self.client.get('/api/v1/presence_start_end/11')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertListEqual(data, [
            ['Mon', 33134.0, 57257.0],
            ['Tue', 33590.0, 50154.0],
            ['Wed', 33206.0, 58527.0],
            ['Thu', 35602.0, 58586.0],
            ['Fri', 47816.0, 54242.0],
            ['Sat', 0, 0],
            ['Sun', 0, 0]
        ])

    def test_weekly_mean_presence_view(self):
        """
        Test weekly_mean_presence_view.
        """
        resp = self.client.get('/api/v1/weekly_mean_presence/2')
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertDictEqual(data, {
            'status': 404,
            'message': 'User 2 not found!'
        })

        resp = self.client.get('/api/v1/weekly_mean_presence/10')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertListEqual(data, [
            ['Activity', 'Total hours'],
            ['Worked hours', 21.43],
            ['Off hours', 146.16]
        ])

        resp = self.client.get('/api/v1/weekly_mean_presence/11')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertListEqual(data[1], ['Worked hours', 26.3])
        self.assertEqual(data[2][1], 141.29)


class PresenceAnalyzerUtilsTestCase(unittest.TestCase):
    """
    Utility functions tests.
    """

    def setUp(self):
        """
        Before each test, set up a environment.
        """
        main.app.config.update({'DATA_CSV': TEST_DATA_CSV})
        main.app.config.update({'USERS_XML': TEST_DATA_XML})

    def tearDown(self):
        """
        Get rid of unused objects after each test.
        """
        pass

    def test_sum_timedelta(self):
        """
        Test converting timedelta to hours.
        """
        delta = utils.sum_timedelta(timedelta(hours=168))
        self.assertEqual(delta, 168.0)

        delta = utils.sum_timedelta(timedelta(days=9, hours=9, seconds=99,
                                              milliseconds=9999))
        self.assertEqual(delta, 225.1)

        delta = utils.sum_timedelta(timedelta(days=3, hours=5, seconds=500))
        self.assertEqual(delta, 77.8)

    def test_sum_intervals(self):
        """
        Test summing intervals.
        """
        intervals = [29508.076923076922, 28530.076923076922, 29702.75,
                     29721.833333333332, 29069.272727272728, 45037.0, 0]
        self.assertTupleEqual(utils.sum_intervals(intervals), (53.12, 114.47))

        intervals = [33134.0, 57257.0, 33590.0, 50154.0, 33206.0, 58527.0]
        self.assertTupleEqual(utils.sum_intervals(intervals), (73.51, 94.8))

        intervals = [0, 0, 56.0, 0, 0, 27.0]
        self.assertTupleEqual(utils.sum_intervals(intervals), (0.1, 167.58))

    def test_cache(self):
        """
        Test caching decorator.
        """
        utils.CACHE = {}
        self.assertDictEqual(utils.CACHE, {})
        data, function = utils.get_data(), utils.get_data.__name__
        key = hashlib.sha1(function).hexdigest()

        self.assertIn(key, utils.CACHE)
        self.assertDictEqual(data, utils.CACHE[key]['data'])
        cached_time = utils.CACHE[key]['time']
        utils.get_data()
        self.assertEqual(cached_time, utils.CACHE[key]['time'])
        time.sleep(1)
        utils.get_data()
        self.assertNotEqual(cached_time, utils.CACHE[key]['time'])
        utils.CACHE[key]['data'] = 'Lorem Ipsum is simply dummy text'
        self.assertNotEqual(utils.CACHE[key]['data'], data)
        utils.CACHE = {}

    def test_get_users_from_xml(self):
        """
        Test extracting user informations from xml.
        """
        data = utils.get_users_from_xml()
        self.assertDictEqual(data, {
            11: {
                'avatar': 'https://intranet.stxnext.pl/api/images/users/11',
                'name': 'Maciej D.'
            },
            10: {
                'avatar': 'https://intranet.stxnext.pl/api/images/users/10',
                'name': 'Maciej Z.'
            }
        })

    def test_get_data(self):
        """
        Test parsing of CSV file.
        """
        data = utils.get_data()
        self.assertIsInstance(data, dict)
        self.assertItemsEqual(data.keys(), [10, 11])
        sample_date = datetime.date(2013, 9, 10)
        self.assertIn(sample_date, data[10])
        self.assertItemsEqual(data[10][sample_date].keys(), ['start', 'end'])
        self.assertEqual(
            data[10][sample_date]['start'],
            datetime.time(9, 39, 5)
        )

    def test_group_by_weekday(self):
        """
        Test gruping items by weekday.
        """
        data = utils.get_data()
        user_data = utils.group_by_weekday(data[10])
        self.assertIsInstance(user_data, list)
        self.assertEqual(len(user_data), 7)
        self.assertEqual(sum(len(inner) for inner in user_data), 3)

    def test_seconds_since_midnight(self):
        """
        Test calculating seconds since midnight.
        """
        time = datetime.datetime.strptime('1:00:00', '%H:%M:%S').time()
        self.assertEqual(utils.seconds_since_midnight(time), 3600)

        time = datetime.datetime.strptime('23:00:00', '%H:%M:%S').time()
        self.assertEqual(utils.seconds_since_midnight(time), 82800)

        time = datetime.datetime.strptime('12:30:00', '%H:%M:%S').time()
        self.assertEqual(utils.seconds_since_midnight(time), 45000)

        time = datetime.datetime.strptime('05:59:59', '%H:%M:%S').time()
        self.assertEqual(utils.seconds_since_midnight(time), 21599)

    def test_interval(self):
        """
        Test interval calculatuion.
        """
        start = datetime.datetime.strptime('5:00:00', '%H:%M:%S').time()
        end = datetime.datetime.strptime('10:00:00', '%H:%M:%S').time()
        self.assertEqual(utils.interval(start, end), 18000)

        start = datetime.datetime.strptime('00:00:00', '%H:%M:%S').time()
        end = start
        self.assertIs(utils.interval(start, end), 0)

        start = datetime.datetime.strptime('05:59:59', '%H:%M:%S').time()
        end = datetime.datetime.strptime('12:30:00', '%H:%M:%S').time()
        self.assertEqual(utils.interval(start, end), 23401)

    def test_mean(self):
        """
        Test calculating mean.
        """
        self.assertEqual(utils.mean([3, 3, 3]), 3)
        self.assertEqual(utils.mean([1, 2, 3, 4, 5, 6, 7]), 4)
        self.assertEqual(utils.mean([0]), 0)
        self.assertAlmostEqual(utils.mean([0.5, 0.6, 1]), 0.7)
        self.assertAlmostEqual(utils.mean([0.3, 0.3, 0.3, 0.5, 0.5, 0.5]), 0.4)
        self.assertEqual(utils.mean([0.5, -1, 0.9, 0.5, -6]), -1.02)

    def test_group_start_end_by_weekday(self):
        """
        Test gruping presence entrences/leaves by weekday.
        """
        data = utils.get_data()
        user_data = utils.group_start_end_by_weekday(data[10])
        self.assertIsInstance(user_data, list)
        self.assertIsInstance(user_data[0], dict)
        self.assertEqual(3, len([
            interval for interval in user_data
            if interval['start'] and interval['end']
            ]))
        self.assertFalse(user_data[0]['start'])
        self.assertIn(34745, user_data[1]['start'])
        self.assertIn(62631, user_data[3]['end'])

        user_data = utils.group_start_end_by_weekday(data[11])
        self.assertEqual(5, len([
            interval for interval in user_data
            if interval['start'] and interval['end']
            ]))
        self.assertFalse(user_data[5]['start'])
        self.assertIn(33134, user_data[0]['start'])
        self.assertIn(54242, user_data[4]['end'])


def suite():
    """
    Default test suite.
    """
    base_suite = unittest.TestSuite()
    base_suite.addTest(unittest.makeSuite(PresenceAnalyzerViewsTestCase))
    base_suite.addTest(unittest.makeSuite(PresenceAnalyzerUtilsTestCase))
    return base_suite


if __name__ == '__main__':
    unittest.main()
