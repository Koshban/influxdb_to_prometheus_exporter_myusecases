from influxdb_client import InfluxDBClient
from influxdb_client.client.query_api import QueryApi
import time
import json
import common.connections as connections
import pandas as pd
from prometheus_client import Gauge, CollectorRegistry, push_to_gateway
import common.SLOqueries


# Configure query and execution frequency
query = common.SLOqueries.queries
execution_frequency = 900  # 900 seconds = 15 minutes

# Connect to InfluxDB
client = InfluxDBClient(url=connections.url, token="your-token", org="your-org")

# Get query client
query_api = client.query_api()

# Function to execute the query and process the result
def execute_query():
  results = query_api.query_data_frame(query)

  if isinstance(results, pd.DataFrame):
    json_output = results.to_json(orient="records", date_format="iso")
  elif isinstance(results, list):
    # Extract data from FluxTable objects
    result_data = [
      {
        "messageType": record.get_value("messageType"),
        "95tile": record.get_value("95tile"),
      }
      for table in json_output for record in table.records
      ]
    json_output = json.dumps(result_data)    
  else:
      raise TypeError(f"Unexpected Result type : {type(results)}")
  
  with open(file="queryoutput.json", mode='w', encoding='utf-8') as f_w:
    f_w.write(json_output)

def to_prometheus_format_and_push(json_output):
    # Create a new registry for this batch of metrics
    registry = CollectorRegistry()

    for item in json_output:
        metric_name = item['_measurement']
        labels = ['action', 'flow', 'host', 'instanceName', 'measurementType', 'messageType', 'mode', 'region']
        label_values = [item[label] for label in labels]

        # Create a new Gauge for this metric
        g = Gauge(metric_name, 'Description of gauge', labels, registry=registry)

        # Set the Gauge to the metric value
        g.labels(*label_values).set(item['_value'])

    # Push the metrics to the Pushgateway
    push_to_gateway('localhost:9091', job='some_job', registry=registry)
# Loop to execute the query at the specified frequency
while True:
    execute_query()
    time.sleep(execution_frequency)