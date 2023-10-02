import unittest
from unittest.mock import Mock, patch
from VSC.influxdb_to_prometheus_exporter_myusecases.src.export_with_threads.export_multi_query import InfluxDBClientWrapper, PrometheusPusher, QueryExecutor

class TestInfluxdbExporter(unittest.TestCase):
    @patch('VSC.influxdb_to_prometheus_exporter_myusecases.src.export_with_threads.export_multi_query.InfluxDBClient', autospec=True)
    def test_InfluxDBClientWrapper(self, MockInfluxDBClient):
        client = InfluxDBClientWrapper('host', 'port', 'username', 'password', 'database')
        client.query('query')
        MockInfluxDBClient().query.assert_called_once_with('query')

    @patch('VSC.influxdb_to_prometheus_exporter_myusecases.src.export_with_threads.export_multi_query.requests.post', autospec=True)
    def test_PrometheusPusher(self, mock_post):
        pusher = PrometheusPusher('pushgateway_url')
        pusher.push('prometheus_data')
        mock_post.assert_called_once()

    @patch('VSC.influxdb_to_prometheus_exporter_myusecases.src.export_with_threads.export_multi_query.InfluxDBClientWrapper', autospec=True)
    @patch('VSC.influxdb_to_prometheus_exporter_myusecases.src.export_with_threads.export_multi_query.PrometheusPusher', autospec=True)
    @patch('VSC.influxdb_to_prometheus_exporter_myusecases.src.export_with_threads.export_multi_query.threading.Thread', autospec=True)
    def test_QueryExecutor(self, mock_Thread, mock_InfluxDBClientWrapper, mock_PrometheusPusher):
        executor = QueryExecutor(mock_InfluxDBClientWrapper(), mock_PrometheusPusher())
        executor.execute_query({'query': 'query', 'frequency': 10})
        mock_Thread.assert_called()

if __name__ == '__main__':
    unittest.main()