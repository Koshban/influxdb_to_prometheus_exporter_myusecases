import os
import json
import logging
from datetime import datetime
from fastapi import FastAPI, Request
from influxdb_client import InfluxDBClient
from prometheus_client import Gauge, generate_latest, CollectorRegistry
from prometheus_client.core import GaugeMetricFamily
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
import common.connections as connections
import common.influxqueries
from fastapi.responses import Response
from uvicorn import run
import requests
import atexit
import ssl

"""
This script sets up a logging for the application, configures and starts a FastAPI app, and sets up InfluxDB client configuration details.
It also contains functions to execute queries on the InfluxDB, schedule these queries, and handle endpoints for getting and posting metrics.
"""

# Add SSL to Serve Over HTTPS
ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
ssl_context.load_cert_chain("path/to/localhost.crt", "path/to/localhost.key")

# The log file name
script_name = os.path.splitext(os.path.basename(__file__))[0]
timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
log_filename = ("/home/koshban/mylogs/{script_name}_{timestamp}.log")
# Configure logging
logging.basicConfig(filename=f'{log_filename}', level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Global registry for Prometheus metrics
prom_registry = CollectorRegistry(auto_describe=True)
# Create a Gauge for each metric in the global registry
metrics_dict = { 
  metric_name: Gauge(metric_name, 'Description of gauge', ['soapid', 'region'], registry=prom_registry)
  for metric_name in common.influxqueries.queries.keys()
}

class CustomCollector(object):
    def __init__(self, metrics_dict):
        self.metrics_dict = metrics_dict

    def collect(self):
        for label_values, gauge in self.metrics_dict.items():
            soapid, region = label_values
            metric = GaugeMetricFamily('metric_name', 'Description of gauge', labels=['soapid', 'region'])
        samples = list(gauge.collect())[0].samples
        if len(samples) > 0:
            _value = samples[0].value
            metric.add_metric([soapid, region], _value)
            yield metric

# FastAPI app
app = FastAPI()

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
    logging.exception(f"Error executing InfluxDB query: {str(e)}")
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
    logging.info(f"Running task: {task.__name__}")
    tables = execute_query(client, query)
    if tables is not None:
      logging.info(f"Query result: {tables}")
      for table in tables:
        for record in table.records:
          soapid = record.values.get('soapid', 'default_soapid')
          region = record.values.get('region', 'default_region')

          _value = record.values.get('_value', 0.0)
          if _value is None:
              _value = 0
          # Update the metrics
          if (soapid, region) in metrics_dict:
              metrics_dict[(soapid, region)].set(_value)
          # metrics_dict[metric_name].labels(*label_values).set(_value)

          # Send the data to the specified URL
          endpoint = "https://localhost:8000/koshban-trading-metrics"
          data = {'value': _value, 'labels': ['soapid', 'region']}
          logging.info("Inside task. data is : {data} and JSON format is :", json.dumps(data, indent=4))
          if data:
            response = requests.post(endpoint, data=json.dumps(data), headers={'Content-Type': 'application/json'})
            logging.info(f"Sent data to {endpoint}, received status code: {response.status_code}")

  scheduler.add_job(task, 'interval', minutes=frequency)
  logging.info(f"Scheduled task: {task.__name__} to run every {frequency} minutes")

@app.on_event("startup")
async def startup():
  """
  Startup event for the FastAPI app. This function creates an InfluxDB client and starts the query tasks.
  """
  client = InfluxDBClient(connections.influxdbconndetails)
  for metric_name, query_dict in common.influxqueries.queries.items():
    query_and_send(client, metric_name, query_dict['query'], query_dict['frequency'])
  prom_registry.register(CustomCollector(metrics_dict)) 

@app.get('/koshban-trading-metrics')
async def get_metrics():
  """
  Endpoint for getting metrics. This function returns the latest metrics.

  Returns:
  Response: A Response object containing the latest metrics.
  """
  metrics = generate_latest(prom_registry)
  logging.info(f"Generated metrics: {metrics}")
  return Response(generate_latest(prom_registry), media_type='text/plain')

@app.post('/koshban-trading-metrics')
async def post_metrics(request: Request, data: dict):
  """
  Endpoint for posting metrics. This function logs and prints the received data.

  Parameters:
  data (dict): The data received in the POST request.

  Returns:
  str: A message indicating successful receipt of data.
  """
  client_host = request.client.host
  user_agent = request.headers.get('User-Agent')
  logging.info(f"Received POST request at /koshban-trading-metrics from {client_host} with User-Agent: {user_agent} and data: {data}")
  print(data)
  return 'Data received and printed!'

def main():
  """
  Main function to start the FastAPI app.
  """
  run("withbg_job:app", host="0.0.0.0", port=8000, 
      log_level="info",
      ssl_keyfile="/home/koshban/mykeys/keyfile.pem", 
      ssl_certfile="/home/koshban/mykeys/certfile.pem")

if __name__ == "__main__":
  main()