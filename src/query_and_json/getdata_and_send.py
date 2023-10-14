from influxdb_client import InfluxDBClient
from influxdb_client.client.query_api import QueryApi
from prometheus_client import Gauge, CollectorRegistry, push_to_gateway
import pandas as pd
import json
import threading
import time
import common.connections as connections
import common.SLOqueries

class QueryExecutor:
  def __init__(self, client):
    self.client = client
    
  def execute_query(self, query):
    try:
      results = self.client.query_data_frame(query)

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

class PrometheusPusher:
  def __init__(self, gateway, job):
    self.gateway = gateway
    self.job = job
  
  def push_to_prometheus(self, json_output):
    try:
      registry = CollectorRegistry()

      for item in json_output:
          metric_name = item['_measurement']
          labels = ['action', 'flow', 'host', 'instanceName', 'measurementType', 'messageType', 'mode', 'region']
          label_values = [item[label] for label in labels]

          g = Gauge(metric_name, 'Description of gauge', labels, registry=registry)
          g.labels(*label_values).set(item['_value'])

      push_to_gateway(self.gateway, job=self.job, registry=registry)
    except Exception as e:
      print(f"Error while pushing to Prometheus: {str(e)}")

def worker(query_executor, prometheus_pusher, query, frequency, lock):
  while True:
    with lock:
      json_output = query_executor.execute_query(query)
      if json_output is not None:
        prometheus_pusher.push_to_prometheus(json.loads(json_output))
    time.sleep(frequency)

def main():
  client = InfluxDBClient(url=connections.url, token="your-token", org="your-org")
  query_executor = QueryExecutor(client)
  prometheus_pusher = PrometheusPusher('localhost:9091', 'some_job')
  lock = threading.Lock()

  for query_dict in common.SLOqueries.queries:
    query_thread = threading.Thread(target=worker, args=(query_executor, prometheus_pusher, query_dict['query'], query_dict['frequency'], lock))
    query_thread.start()

if __name__ == "__main__":
  main()