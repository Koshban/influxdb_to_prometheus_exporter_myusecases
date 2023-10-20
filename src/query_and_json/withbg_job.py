import os
import json
import logging
from datetime import datetime
from fastapi import FastAPI
from influxdb_client import InfluxDBClient
from prometheus_client import Gauge, generate_latest, REGISTRY, CollectorRegistry
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
import common.connections as connections
import common.influxqueries
from fastapi.responses import Response
from uvicorn import run
import requests
import atexit

"""
This script sets up a logging for the application, configures and starts a FastAPI app, and sets up InfluxDB client configuration details.
It also contains functions to execute queries on the InfluxDB, schedule these queries, and handle endpoints for getting and posting metrics.
"""

# Get the script name (without the extension) for log file
script_name = os.path.splitext(os.path.basename(__file__))[0]
# Generate a timestamp for log file
timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
# The log file name
log_filename = ("/home/koshban/mylogs/{script_name}_{timestamp}.log")
# Configure logging
logging.basicConfig(filename=f'{log_filename}', level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# FastAPI app
app = FastAPI()

# Global registry for Prometheus metrics
prom_registry = CollectorRegistry(auto_describe=True)

# InfluxDB client configuration details
INFLUXDB_URL = os.getenv("INFLUXDB_URL")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG")

# Create a Gauge for each metric in the global registry
metrics_dict = { 
  metric_name: Gauge(metric_name, 'Description of gauge', ['soapid', 'region'], registry=prom_registry)
  for metric_name in common.influxqueries.queries.keys()
}

def execute_query(client, query):
  """
  Execute query on InfluxDB.

  Parameters:
  client (InfluxDBClient): The InfluxDB client.
  query (str): The query to execute.

  Returns:
  tables: The result of the query.
  """
  query_api = client.query_api()
  try:
    tables = query_api.query(query)
    return tables
  except Exception as e:
    logging.error(f"Error executing InfluxDB query: {str(e)}")
    return None

def query_and_send(client, metric_name, query, frequency):
  """
  Schedule and execute a query task.

  Parameters:
  client (InfluxDBClient): The InfluxDB client.
  metric_name (str): The name of the metric.
  query (str): The query to execute.
  frequency (int): The frequency at which to execute the query in minutes.
  """
  scheduler = BackgroundScheduler()
  scheduler.start()
  atexit.register(lambda: scheduler.shutdown())

  def task():
    """
    The task to execute. This task executes a query, logs the result, sends the result to a URL, and updates a metric.
    """
    tables = execute_query(client, query)
    if tables is not None:
      logging.info(f"Query result: {tables}")
      for table in tables:
        for record in table.records:
          labels = ['TypeSet', 'soapid', 'region']
          label_values = ['mymsg', '129080', 'All']

          _value = record.values.get('_value', 0.0)
          if _value is None:
              _value = 0
          metrics_dict[metric_name].labels(*label_values).set(_value)

          # Send the data to the specified URL
          endpoint = "http://abcd.com/koshban-trading-metrics"
          data = {'value': _value, 'labels': label_values}
          requests.post(endpoint, data=json.dumps(data), headers={'Content-Type': 'application/json'})

  scheduler.add_job(task, 'interval', minutes=frequency)

@app.on_event("startup")
async def startup():
  """
  Startup event for the FastAPI app. This function creates an InfluxDB client and starts the query tasks.
  """
  client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
  for metric_name, query_dict in common.influxqueries.queries.items():
    query_and_send(client, metric_name, query_dict['query'], query_dict['frequency'])

@app.get('/koshban-trading-metrics')
async def get_metrics():
  """
  Endpoint for getting metrics. This function returns the latest metrics.

  Returns:
  Response: A Response object containing the latest metrics.
  """
  return Response(generate_latest(prom_registry), media_type='text/plain')

@app.post('/koshban-trading-metrics')
async def post_metrics(data: dict):
  """
  Endpoint for posting metrics. This function logs and prints the received data.

  Parameters:
  data (dict): The data received in the POST request.

  Returns:
  str: A message indicating successful receipt of data.
  """
  print(data)
  logging.info(f"Received POST request at /koshban-trading-metrics with data: {data}")
  return 'Data received and printed!'

def main():
  """
  Main function to start the FastAPI app.
  """
  run("main:app", host="0.0.0.0", port=8000, log_level="info")

if __name__ == "__main__":
  main()