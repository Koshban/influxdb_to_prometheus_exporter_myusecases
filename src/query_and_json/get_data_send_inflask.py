from flask import Flask, Response, request
from influxdb_client import InfluxDBClient, InfluxDBError
from influxdb_client.client.query_api import QueryApi
from prometheus_client import Gauge, generate_latest, REGISTRY
import pandas as pd
import json
import threading
import time
import common.connections as connections
import common.SLOqueries

app = Flask(__name__)

# Global registry for Prometheus metrics
registry = REGISTRY

class QueryExecutor:
  def __init__(self, client):
    self.client = client
    
  def execute_query(self, query):
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
    except InfluxDBError as e:
      print(f"InfluxDBError while executing query: {str(e)}")
      return None
    except Exception as e:
      print(f"Error while executing query: {str(e)}")
      return None

def worker(query_executor, metric_name, query, frequency):
  while True:
    try:
      json_output = query_executor.execute_query(query)
      if json_output is not None:
        for item in json.loads(json_output):
            labels = ['action', 'flow', 'host', 'instanceName', 'measurementType', 'messageType', 'mode', 'region']
            label_values = [item.get(label) for label in labels]

            g = Gauge(metric_name, 'Description of gauge', labels, registry=registry)
            g.labels(*label_values).set(item.get('_value', 0))
    except Exception as e:
      print(f"Error in worker thread: {str(e)}")

    time.sleep(frequency / 1000)  # convert frequency from ms to s

@app.route("/start", methods=['GET'])
def start():
  try:
    client = InfluxDBClient(url=connections.url, token="your-token", org="your-org")
    query_executor = QueryExecutor(client)

    for metric_name, query_dict in common.SLOqueries.queries.items():
      query_thread = threading.Thread(target=worker, args=(query_executor, metric_name, query_dict['query'], query_dict['frequency']))
      query_thread.start()
    
    return "Worker threads started!"
  except Exception as e:
    return f"Error while starting worker threads: {str(e)}", 500

@app.route('/koshban-trading-metrics', methods=['GET'])
def metrics():
    try:
        return Response(generate_latest(registry), mimetype='text/plain')
    except Exception as e:
        return f"Error while generating metrics: {str(e)}", 500

if __name__ == "__main__":
  try:
    app.run(port=8888)
  except Exception as e:
    print(f"Error while starting Flask app: {str(e)}")