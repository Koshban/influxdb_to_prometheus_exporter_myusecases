import pytest
from unittest.mock import patch
from flask import Flask
from app import app  # Assuming the Flask application is in a file called app.py

# Create a fixture for the Flask application.
@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

# Test the /start endpoint
@patch('app.QueryExecutor')  # Mock the QueryExecutor class
@patch('app.InfluxDBClient')  # Mock the InfluxDB client
def test_start(mock_client, mock_executor, client):
    mock_client.return_value = None  # No actual client will be created
    mock_executor.return_value = None  # No actual executor will be created

    response = client.get('/start')
    assert response.status_code == 200
    assert response.data.decode() == "Worker threads started!"

# Test the /koshban-trading-metrics endpoint with a GET request
def test_metrics_get(client):
    response = client.get('/koshban-trading-metrics')
    assert response.status_code == 200

# Test the /koshban-trading-metrics endpoint with a POST request
def test_metrics_post(client):
    response = client.post('/koshban-trading-metrics', json={"test": "data"})
    assert response.status_code == 200
    assert response.data.decode() == "Data received and printed!"