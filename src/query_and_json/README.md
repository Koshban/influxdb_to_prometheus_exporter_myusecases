# Flask Application with InfluxDB and Prometheus

This project is a Flask web application that interacts with InfluxDB and Prometheus to execute queries, log results, and expose metrics.

## Getting Started

To get the application running, you need to have Flask, InfluxDB, and Prometheus installed on your system.

### Prerequisites

- Flask
- InfluxDBClient
- Prometheus_client
- Pandas

You can install these using pip:

```bash
pip install flask influxdb-client prometheus-client pandas
```

### Usage

This application has two main routes:

/start: starts worker threads that execute InfluxDB queries and update Prometheus metrics.
/koshban-trading-metrics: returns Prometheus metrics in text format for GET requests and prints POSTed data for POST requests.

### Understanding the Code

The code is primarily composed of a Flask application, a QueryExecutor class, and a worker function.

QueryExecutor: This class handles the execution of queries against InfluxDB. It has a method execute_query which executes a query against InfluxDB and returns the results.
worker: This is a function that executes a query at a regular interval and updates the associated Prometheus metric.
Flask application: The Flask application has two routes as mentioned above. The application starts by running app.run(port=8888).

## License

This project is licensed under the MIT License.
