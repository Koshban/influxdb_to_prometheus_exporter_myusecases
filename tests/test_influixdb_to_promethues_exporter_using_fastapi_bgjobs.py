import pytest
from unittest.mock import MagicMock
from influxdb_client import InfluxDBClient
from src.query_and_json.influixdb_to_promethues_exporter_using_fastapi_bgjobs import execute_query 

def test_execute_query_success():
    client = MagicMock(spec=InfluxDBClient)
    query_api = MagicMock()
    client.query_api.return_value = query_api
    query_api.query.return_value = "expected result"
    
    result = execute_query(client, "SELECT * FROM my_table")
    
    assert result == "expected result"
    query_api.query.assert_called_once_with("SELECT * FROM my_table")

def test_execute_query_error():
    client = MagicMock(spec=InfluxDBClient)
    query_api = MagicMock()
    client.query_api.return_value = query_api
    query_api.query.side_effect = Exception("DB Error")
    
    result = execute_query(client, "SELECT * FROM my_table")
    
    assert result is None
    query_api.query.assert_called_once_with("SELECT * FROM my_table")