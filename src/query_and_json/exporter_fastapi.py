import os
import time
import threading
import json
import logging
from datetime import datetime
from fastapi import FastAPI
from influxdb_client import InfluxDBClient
from prometheus_client import Gauge, generate_latest, REGISTRY, CollectorRegistry
import pandas as pd
import asyncio
import common.connections as connections
import common.influxqueries
from fastapi.responses import Response
from uvicorn import run

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
  query_api = client.query_api()
  try:
    tables = query_api.query(query)
    return tables
  except Exception as e:
    logging.error(f"Error executing InfluxDB query: {str(e)}")
    return None

async def worker(client, metric_name, query, frequency):
  while True:
    tables = execute_query(client, query)
    if tables is not None:
      logging.info(f"Query result: {tables}")
      for table in tables:
        for record in table.records:
          labels = ['TypeSet', 'soapid', 'region']
          label_values = ['mymsg', '129080', 'All']

          # Update the Gauge value
        #   metrics_dict[metric_name].labels(*label_values).set(record.get_value('_value', 0))
        _value = record.values.get('_value', 0.0)
        if _value is None:
            _value = 0
        metrics_dict[metric_name].labels(*label_values).set(_value)
    await asyncio.sleep(frequency / 1000)  # convert frequency from ms to s

@app.on_event("startup")
async def startup():
  client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
  for metric_name, query_dict in common.influxqueries.queries.items():
    asyncio.create_task(worker(client, metric_name, query_dict['query'], query_dict['frequency']))

@app.get('/koshban-trading-metrics')
async def get_metrics():
  return Response(generate_latest(prom_registry), media_type='text/plain')

@app.post('/koshban-trading-metrics')
async def post_metrics(data: dict):
  print(data)
  logging.info(f"Received POST request at /koshban-trading-metrics with data: {data}")
  return 'Data received and printed!'

def main():
  run("main:app", host="0.0.0.0", port=8000, log_level="info")

if __name__ == "__main__":
  main()