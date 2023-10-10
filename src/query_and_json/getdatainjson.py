from influxdb_client import InfluxDBClient
from influxdb_client.client.query_api import QueryApi
import time
import json
import common.connections as connections

# Configure query and execution frequency
query = '''
from(bucket: "default")
  |> range(start: 1695907248642ms, stop: 1695916384594ms)
  |> filter(fn: (r) => r._measurement == "talon" and r.region =~ /^USS/ and r.latencyType == "client.update.message.loadAndSend")
  |> keep(columns: ["95tile", "messageType"])
  |> group(columns: ["messageType"])
'''
execution_frequency = 900  # 900 seconds = 15 minutes

# Connect to InfluxDB
client = InfluxDBClient(url=connections.influxdbconn, token="your-token", org="your-org")

# Get query client
query_api = client.query_api()

# Function to execute the query and process the result
def execute_query():
    result = query_api.query(query)
    # Convert the result to a list of dictionaries and create a JSON object
    data_points = [record.values for table in result for record in table.records]
    json_output = json.dumps(data_points)
    print(json_output)

# Loop to execute the query at the specified frequency
while True:
    execute_query()
    time.sleep(execution_frequency)