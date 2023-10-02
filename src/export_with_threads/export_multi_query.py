import time
import threading
import requests
from influxdb import InfluxDBClient
import logging
from requests.exceptions import RequestException
from influxdb.exceptions import InfluxDBClientError, InfluxDBServerError
import VSC.influxdb_to_prometheus_exporter_myusecases.common.exporterconfig as exporterconfig
import VSC.influxdb_to_prometheus_exporter_myusecases.common.SLOqueries as SLOqueries
import VSC.influxdb_to_prometheus_exporter_myusecases.common.connections as connections

# Configure logging
logging.basicConfig(level=logging.INFO)

class InfluxDBClientWrapper:
    def __init__(self, host, port, username, password, database):
        self.client = InfluxDBClient(host, port, username, password, database)

    def query(self, query):
        try:
            result = self.client.query(query)
            return list(result.get_points())
        except (InfluxDBClientError, InfluxDBServerError) as e:
            logging.error(f"Failed to execute query: {e}")
            return []

class PrometheusPusher:
    def __init__(self, pushgateway_url):
        self.pushgateway_url = pushgateway_url

    def push(self, prometheus_data):
        try:
            response = requests.post(self.pushgateway_url, data=prometheus_data)
            return response.status_code
        except RequestException as e:
            logging.error(f"Failed to push data: {e}")
            return None

class QueryExecutor:
    def __init__(self, influxdb_client, prometheus_pusher):
        self.influxdb_client = influxdb_client
        self.prometheus_pusher = prometheus_pusher
        self.lock = threading.Lock()
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def execute_query(self, query_info):
        while not self._stop_event.is_set():
            data_points = self.influxdb_client.query(query_info["query"])
            prometheus_data = ""
            for data_point in data_points:
                for key, value in data_point.items():
                    if isinstance(value, (int, float)):
                        prometheus_data += f"# TYPE {key} gauge\n{key} {value}\n"
            
            with self.lock:
                status_code = self.prometheus_pusher.push(prometheus_data)
                if status_code == 200:
                    logging.info(f"Data from query '{query_info['query']}' pushed successfully!")
                else:
                    logging.error(f"Failed to push data from query '{query_info['query']}': {status_code}")

            time.sleep(query_info["frequency"])

def main():
    influxdb_client = InfluxDBClientWrapper(connections.influxdbconn)
    prometheus_pusher = PrometheusPusher(exporterconfig.prometheus_pushgateway_url)
    query_executor = QueryExecutor(influxdb_client, prometheus_pusher)

    threads = []
    for query_info in SLOqueries.queries.values():
        thread = threading.Thread(target=query_executor.execute_query, args=(query_info,))
        thread.start()
        threads.append(thread)

    try:
        for thread in threads:
            thread.join()
    except KeyboardInterrupt:
        logging.info("Stopping threads...")
        query_executor.stop()
        for thread in threads:
            thread.join()

if __name__ == "__main__":
    main()