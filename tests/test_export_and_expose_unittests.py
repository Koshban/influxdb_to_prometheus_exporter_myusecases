import unittest
from unittest.mock import Mock, patch
from VSC.influxdb_to_prometheus_exporter_myusecases.src.query_and_export.export_and_expose import execute_query, push_to_prometheus, execute_queries

class TestInfluxdbExporter(unittest.TestCase):
    @patch('VSC.influxdb_to_prometheus_exporter_myusecases.src.query_and_export.export_and_expose.InfluxDBClient', autospec=True)
    def test_execute_query(self, MockInfluxDBClient):
        metric = Mock()
        execute_query('query_name', 'query', metric)
        MockInfluxDBClient().query.assert_called_once_with('query')
        metric.set.assert_called()

    @patch('VSC.influxdb_to_prometheus_exporter_myusecases.src.query_and_export.export_and_expose.requests.post', autospec=True)
    def test_push_to_prometheus(self, mock_post):
        push_to_prometheus(['metric1', 'metric2'])
        mock_post.assert_called_once()

    @patch('VSC.influxdb_to_prometheus_exporter_myusecases.src.query_and_export.export_and_expose.execute_query', autospec=True)
    @patch('VSC.influxdb_to_prometheus_exporter_myusecases.src.query_and_export.export_and_expose.push_to_prometheus', autospec=True)
    def test_execute_queries(self, mock_execute_query, mock_push_to_prometheus):
        execute_queries()
        mock_execute_query.assert_called()
        mock_push_to_prometheus.assert_called()

if __name__ == '__main__':
    unittest.main()