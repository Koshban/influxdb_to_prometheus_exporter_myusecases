import os
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
log_filename = (f"/home/koshban/mylogs/{script_name}_{timestamp}.log")
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
            metric = GaugeMetricFamily('metric_name', 'Data Exporter from influxDB', labels=['soapid', 'region'])
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
  
def reset_metrics(metrics_dict, prom_registry):
  for metric_name in list(metrics_dict.keys()):
    gauge: Gauge = metrics_dict[metric_name]
    labelnames = gauge._labelnames
    # Remove the old Gauge from the registry
    prom_registry.unregister(gauge)
    # Recreate the Gauge and replace the old one in metrics_dict
    metrics_dict[metric_name] = Gauge(metric_name, 'Data Exporter from influxDB', labelnames=labelnames, registry=prom_registry)

@app.on_event("startup")
async def startup():
  """
  Startup event for the FastAPI app. This function creates an InfluxDB client and starts the query tasks.
  """
  prom_registry.register(CustomCollector(metrics_dict)) 

@app.get('/koshban-trading-metrics')
async def get_metrics():
  """
  Endpoint for getting metrics. This function performs the queries, updates the metrics,
  and returns the latest metrics.

  Returns:
  Response: A Response object containing the latest metrics.
  """
  client = InfluxDBClient(connections.influxdbconndetails)
  

  for metric_name, query_dict in common.influxqueries.queries.items():
    tables = execute_query(client, query_dict['query'])
    if tables is not None:
      for table in tables:
        for record in table.records:
          # Log the record to inspect the actual keys
          logging.debug(f"Record: {record.values}")

          soapid = record.get_value('soapid')  
          region = record.get_value('region')  

          _value = record.get_value('_value', 0.0)
          if _value is None:  # ignore None records
              continue
          
          # Add a check to ensure that soapid and region are not the default values
          if soapid == 'default_soapid' or region == 'default_region':
              logging.error(f"Default values are being used for soapid or region: soapid={soapid}, region={region}")
              continue

          # Update the metrics
          metrics_dict[metric_name].labels(soapid=soapid, region=region).set(_value)            
  metrics = generate_latest(prom_registry)
  metrics_str = metrics.decode('utf-8')
  response = Response(metrics, media_type='text/plain')
  logging.info(f"Generated metrics: {metrics_str}")
  # Reset the metrics before fetching new data
  reset_metrics(metrics_dict, prom_registry)
  # Check if metrics_dict is not empty
  if not metrics_dict:
    logging.info("metrics_dict is empty. No metrics to log after reset.")
  else:
    # Log the length of metrics_dict
    logging.info(f"metrics_dict contains {len(metrics_dict)} items.")
    logging.info(f"Contents of metrics_dict: {metrics_dict}")
    # Log the reset metrics values (should be zero if reset correctly)
    for metric_name in metrics_dict:
      for label_set, metric in metrics_dict[metric_name]._metrics.items():
        value = metric.get()
        logging.info(f"Metric {metric_name} with labels {label_set} has been reset to: {value}")
  return response

def main():
  """
  Main function to start the FastAPI app.
  """
  run("withbg_job:app", host="0.0.0.0", port=8000, 
      log_level="debug",
      ssl_keyfile="/home/koshban/mykeys/keyfile.pem", 
      ssl_certfile="/home/koshban/mykeys/certfile.pem")

if __name__ == "__main__":
  main()