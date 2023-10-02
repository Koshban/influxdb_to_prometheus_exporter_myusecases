import pytest
from unittest.mock import Mock, patch
from VSC.influxdb_to_prometheus_exporter_myusecases.src.export_with_threads.another_one_with_threads import InfluxDBClientWrapper, PrometheusPusher, QueryExecutor

@patch('VSC.influxdb_to_prometheus_exporter_myusecases.src.export_with_threads.another_one_with_threads.InfluxDBClient')
def test_influxdb_client_wrapper(MockClient):
    wrapper = InfluxDBClientWrapper('host', 'port', 'user', 'pass', 'db')
    wrapper.query('QUERY')
    MockClient().query.assert_called_once()

@patch('VSC.influxdb_to_prometheus_exporter_myusecases.src.export_with_threads.another_one_with_threads.requests.post')
def test_prometheus_pusher(mock_post):
    pusher = PrometheusPusher('url')
    pusher.push('data')
    mock_post.assert_called_once_with('url', data='data')

@patch('VSC.influxdb_to_prometheus_exporter_myusecases.src.export_with_threads.another_one_with_threads.time.sleep')
def test_query_executor(mock_sleep):
    influxdb_client = Mock()
    prometheus_pusher = Mock()
    executor = QueryExecutor(influxdb_client, prometheus_pusher)

    executor.execute_query({'query': 'QUERY', 'frequency': 1})
    influxdb_client.query.assert_called_once_with('QUERY')
    prometheus_pusher.push.assert_called_once()