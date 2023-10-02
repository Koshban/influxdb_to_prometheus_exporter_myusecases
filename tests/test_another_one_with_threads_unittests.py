import unittest
from unittest.mock import Mock, patch
from VSC.influxdb_to_prometheus_exporter_myusecases.src.export_with_threads.another_one_with_threads import InfluxDBClientWrapper, PrometheusPusher, QueryExecutor

class TestInfluxDBClientWrapper(unittest.TestCase):
    @patch('VSC.influxdb_to_prometheus_exporter_myusecases.src.export_with_threads.another_one_with_threads.InfluxDBClient')
    def test_query(self, MockClient):
        wrapper = InfluxDBClientWrapper('host', 'port', 'user', 'pass', 'db')
        wrapper.query('QUERY')
        MockClient().query.assert_called_once()

class TestPrometheusPusher(unittest.TestCase):
    @patch('VSC.influxdb_to_prometheus_exporter_myusecases.src.export_with_threads.another_one_with_threads.requests.post')
    def test_push(self, mock_post):
        pusher = PrometheusPusher('url')
        pusher.push('data')
        mock_post.assert_called_once_with('url', data='data')

class TestQueryExecutor(unittest.TestCase):
    def setUp(self):
        self.influxdb_client = Mock()
        self.prometheus_pusher = Mock()
        self.executor = QueryExecutor(self.influxdb_client, self.prometheus_pusher)

    @patch('VSC.influxdb_to_prometheus_exporter_myusecases.src.export_with_threads.another_one_with_threads.time.sleep')
    def test_execute_query(self, mock_sleep):
        self.executor.execute_query({'query': 'QUERY', 'frequency': 1})
        self.influxdb_client.query.assert_called_once_with('QUERY')
        self.prometheus_pusher.push.assert_called_once()

if __name__ == '__main__':
    unittest.main()