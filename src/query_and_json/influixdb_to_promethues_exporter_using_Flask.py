from flask import Flask, Response, request
from influxdb_client import InfluxDBClient
from influxdb_client.client.query_api import QueryApi
from prometheus_client import Gauge, generate_latest, REGISTRY
import pandas as pd
import json
import threading
import time
import common.connections as connections
import common.influxqueries
import logging
import os
from datetime import datetime

# Get the script name (without the extension)
script_name = os.path.splitext(os.path.basename(__file__))[0]
# Generate a timestamp
timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
# The log file name
log_filename = "/home/koshban/mylogs/{script_name}_{timestamp}.log"
# Configure logging
logging.basicConfig(filename=f'{log_filename}', level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
app = Flask(__name__)

# Global registry for Prometheus metrics
registry = REGISTRY

class QueryExecutor:
  """
  Class to handle execution of queries against InfluxDB.
  """

  def __init__(self, client):
    """
    Constructor for QueryExecutor.
    Args:
      client: InfluxDB client instance.
    """
    self.client = client
    
  def execute_query(self, query):
    """
    Executes a query against InfluxDB and returns the results.

    Args:
      query: A string representing the query to be executed.

    Returns:
      A JSON string representing the result of the query, or None if an error occurred or no data was returned.
    """
    try:
      results = self.client.query_data_frame(query)

      if results is None or (isinstance(results, pd.DataFrame) and results.empty) or (isinstance(results, list) and not results):
        print(f"No data returned from query: {query}")
        return None

      if isinstance(results, pd.DataFrame):
        return results.to_json(orient="records", date_format="iso")
      elif isinstance(results, list):
        result_data = [
          {
            "messageType": record.get_value("messageType"),
            "95tile": record.get_value("95tile"),
          }
          for table in results for record in table.records
        ]
        return json.dumps(result_data)
      else:
        raise TypeError(f"Unexpected Result type : {type(results)}")
    except Exception as e:
      print(f"Error while executing query: {str(e)}")
      return None

def worker(query_executor, metric_name, query, frequency):
  """
  Worker function to execute a query at a regular interval and update the associated Prometheus metric.

  Args:
    query_executor: A QueryExecutor instance to handle query execution.
    metric_name: The name of the Prometheus metric to be updated.
    query: The InfluxDB query to be executed.
    frequency: The frequency at which the query should be executed, in milliseconds.
  """
  while True:
    try:
      json_output = query_executor.execute_query(query)
      if json_output is not None:
        logging.info(f"JSON Output: {json_output}")
        for item in json.loads(json_output):
            labels = ['action', 'flow', 'host', 'instanceName', 'measurementType', 'messageType', 'mode', 'region']
            label_values = [item.get(label) for label in labels]

            g = Gauge(metric_name, 'Description of gauge', labels, registry=registry)
            g.labels(*label_values).set(item.get('_value', 0))
    except Exception as e:
      logging.error(f"Error in worker thread: {str(e)}")

    time.sleep(frequency / 1000)  # convert frequency from ms to s

@app.route("/start", methods=['GET'])
def start():
  """
  Starts the worker threads to execute the InfluxDB queries and update the Prometheus metrics.
  """
  try:
    client = InfluxDBClient(connections.influxdbconndetails)
    query_executor = QueryExecutor(client)

    for metric_name, query_dict in common.influxqueries.queries.items():
      query_thread = threading.Thread(target=worker, args=(query_executor, metric_name, query_dict['query'], query_dict['frequency']))
      query_thread.start()
    
    return "Worker threads started!"
  except Exception as e:
    return f"Error while starting worker threads: {str(e)}", 500

@app.route('/koshban-trading-metrics', methods=['GET', 'POST'])
def metrics():
  """
  Returns the Prometheus metrics in text format for GET requests,
  and prints POSTed data for POST requests.
  """
  if request.method == 'GET':
    try:
      return Response(generate_latest(registry), mimetype='text/plain')
    except Exception as e:
      return f"Error while generating metrics: {str(e)}", 500
  elif request.method == 'POST':
    data = request.get_json()  # Assuming the POSTed data is in JSON format
    print(data)
    return 'Data received and printed!'

if __name__ == "__main__":
  """
  Starts the Flask application.
  """
  try:
    app.run(port=8888)
  except Exception as e:
    print(f"Error while starting Flask app: {str(e)}")