import unittest
from unittest.mock import Mock, patch
from VSC.influxdb_to_prometheus_exporter_myusecases.src.query_and_json.getdatainjson import execute_query

class TestQueryExecutor(unittest.TestCase):
    @patch('VSC.influxdb_to_prometheus_exporter_myusecases.src.query_and_json.getdatainjson.InfluxDBClient', autospec=True)
    def test_execute_query(self, MockInfluxDBClient):
        execute_query()
        MockInfluxDBClient().query.assert_called_once_with('your_query')

if __name__ == '__main__':
    unittest.main()