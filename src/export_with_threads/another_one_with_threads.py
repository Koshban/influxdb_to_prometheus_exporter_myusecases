# import json
# import requests

# # Assume that this is the JSON data we received
# json_data = """
# {
#   "temperature": 23.5,
#   "humidity": 40
# }
# """

# # Parse the JSON data
# data = json.loads(json_data)

# # Construct the data in Prometheus exposition format
# prometheus_data = ""
# for key, value in data.items():
#     prometheus_data += f"# TYPE {key} gauge\n{key} {value}\n"

# # Now we can push this data to a Prometheus Pushgateway
# pushgateway_url = 'http://pushgateway.example.org:9091/metrics/job/my_job'
# response = requests.post(pushgateway_url, data=prometheus_data)

# # Check if push was successful
# if response.status_code == 200:
#     print("Data pushed successfully!")
# else:
#     print(f"Failed to push data: {response.content}")

import time
import threading
import requests
from influxdb import InfluxDBClient
import SLOqueries, config

class InfluxDBClientWrapper:
    def __init__(self, host, port, username, password, database):
        self.client = InfluxDBClient(host, port, username, password, database)

    def query(self, query):
        result = self.client.query(query)
        return list(result.get_points())

class PrometheusPusher:
    def __init__(self, pushgateway_url):
        self.pushgateway_url = pushgateway_url

    def push(self, prometheus_data):
        response = requests.post(self.pushgateway_url, data=prometheus_data)
        return response.status_code

class QueryExecutor:
    def __init__(self, influxdb_client, prometheus_pusher):
        self.influxdb_client = influxdb_client
        self.prometheus_pusher = prometheus_pusher
        self.lock = threading.Lock()

    def execute_query(self, query_info):
        while True:
            data_points = self.influxdb_client.query(query_info["query"])
            prometheus_data = ""
            for data_point in data_points:
                for key, value in data_point.items():
                    if isinstance(value, (int, float)):
                        prometheus_data += f"# TYPE {key} gauge\n{key} {value}\n"
            
            with self.lock:
                status_code = self.prometheus_pusher.push(prometheus_data)
                if status_code == 200:
                    print(f"Data from query '{query_info['query']}' pushed successfully!")
                else:
                    print(f"Failed to push data from query '{query_info['query']}': {status_code}")

            time.sleep(query_info["frequency"])

def main():
    influxdb_client = InfluxDBClientWrapper(config.host, config.port, config.username, config.password, config.database)
    prometheus_pusher = PrometheusPusher(config.pushgateway_url)
    query_executor = QueryExecutor(influxdb_client, prometheus_pusher)

    threads = []
    for query_info in SLOqueries.queries.values():
        thread = threading.Thread(target=query_executor.execute_query, args=(query_info,))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

if __name__ == "__main__":
    main()