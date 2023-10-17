import unittest
from unittest.mock import Mock, patch
from influxdb_client.client.query_api import QueryApi
from pandas import DataFrame
from app import QueryExecutor, worker  # Assuming the application is in a file called app.py

class TestQueryExecutor(unittest.TestCase):
    @patch.object(QueryApi, 'query_data_frame', return_value=DataFrame({"test": [1, 2, 3]}))
    def test_execute_query_success(self, mock_query):
        client = Mock()
        executor = QueryExecutor(client)
        result = executor.execute_query("SELECT * FROM test")
        self.assertIsNotNone(result)
        self.assertEqual(result, '[{"test":1},{"test":2},{"test":3}]')

    @patch.object(QueryApi, 'query_data_frame', return_value=None)
    def test_execute_query_no_data(self, mock_query):
        client = Mock()
        executor = QueryExecutor(client)
        result = executor.execute_query("SELECT * FROM test")
        self.assertIsNone(result)

class TestWorker(unittest.TestCase):
    @patch('app.QueryExecutor.execute_query', return_value='[{"test":1}]')
    @patch('app.Gauge')
    @patch('app.logging.info')
    def test_worker_success(self, mock_logging, mock_gauge, mock_query):
        query_executor = Mock()
        metric_name = "test_metric"
        query = "SELECT * FROM test"
        frequency = 1000
        worker(query_executor, metric_name, query, frequency)
        mock_query.assert_called_once()
        mock_logging.assert_called_once()
        mock_gauge.assert_called_once()

if __name__ == '__main__':
    unittest.main()