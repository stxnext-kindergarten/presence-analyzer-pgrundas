# -*- coding: utf-8 -*-
"""
Presence analyzer unit tests.
"""
import os.path
import json
import datetime
import unittest

from presence_analyzer import main, views, utils


TEST_DATA_CSV = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'test_data.csv'
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

    def test_api_users(self):
        """
        Test users listing.
        """
        resp = self.client.get('/api/v1/users')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertEqual(len(data), 2)
        self.assertDictEqual(data[0], {u'user_id': 10, u'name': u'User 10'})

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
        self.assertEqual(resp.status_code, 404)

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
        self.assertEqual(data[4], [u'Thu', 23705])

        resp = self.client.get('/api/v1/mean_time_weekday/5')
        self.assertEqual(resp.status_code, 404)


class PresenceAnalyzerUtilsTestCase(unittest.TestCase):
    """
    Utility functions tests.
    """

    def setUp(self):
        """
        Before each test, set up a environment.
        """
        main.app.config.update({'DATA_CSV': TEST_DATA_CSV})

    def tearDown(self):
        """
        Get rid of unused objects after each test.
        """
        pass

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
        self.assertIs(utils.interval(start, end),  0)

        start = datetime.datetime.strptime('05:59:59', '%H:%M:%S').time()
        end = datetime.datetime.strptime('12:30:00', '%H:%M:%S').time()
        self.assertEqual(utils.interval(start, end),  23401)

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
