from influxdb_client import InfluxDBClient
from influxdb_client.client.query_api import QueryApi
import time
import json
import common.connections as connections
import pandas as pd

# Configure query and execution frequency
query = '''
from(bucket: "default")
  |> range(start: -10m, stop: now())
  |> filter(fn: (r) => r._measurement == "Macchhar" and r.region =~ /^INDIA$/ and r.latencyType == "client.update.message.loadAndSend")
  |> keep(columns: ["95tile", "messageType"])
  |> group(columns: ["messageType"])
'''
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
        json_output = json.dumps(results)
    else:
        raise TypeError(f"Unexpected Result type : {type(results)}")
    
    with open(file="queryoutput.json", mode='w', encoding='utf-8') as f_w:
        f_w.write(json_output)

# Loop to execute the query at the specified frequency
while True:
    execute_query()
    time.sleep(execution_frequency)