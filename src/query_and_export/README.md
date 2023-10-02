# InfluxDB to Prometheus Exporter in export_and_expose.py

This Python script regularly executes queries on InfluxDB, converts the results into Prometheus metrics, and exposes these metrics via a Prometheus HTTP server. 

## Dependencies

- `influxdb`: A Python client for InfluxDB.
- `prometheus_client`: A Python client for the Prometheus monitoring system.
- `requests`: A simple HTTP library for Python, built for human beings.
- `json`: A Python module for working with JSON data.
- `exporterconfig`: A custom module containing configuration details for the exporter.
- `SLOqueries`: A custom module containing the queries to be executed.

## Usage

The script starts a Prometheus HTTP server, executes the specified queries on InfluxDB at regular intervals, and pushes the results to Prometheus. It uses the `exporterconfig` and `SLOqueries` modules to fetch configuration details and queries respectively.

### Configuration

The `exporterconfig` module should provide the following configuration details:

- `host`: The host of the InfluxDB server.
- `port`: The port of the InfluxDB server.
- `username`: The username for the InfluxDB server.
- `password`: The password for the InfluxDB server.
- `database`: The database to connect to on the InfluxDB server.
- `prometheus_pushgateway_url`: The URL of the Prometheus Pushgateway.
- `prometheusport`: The port for the Prometheus HTTP server.

The `SLOqueries` module should provide the queries to be executed as a dictionary. Each key is a query name and the corresponding value is another dictionary containing the InfluxDB query (`query`) and the frequency at which it should be executed (`frequency`).

### Running the Script

To run the script, use the command:
python3 export_and_expose.py

## Functions

- `execute_query(query_name, query, metric)`: Executes a query on InfluxDB and updates the corresponding Prometheus metric.
- `push_to_prometheus(metrics)`: Pushes the metrics to the Prometheus Pushgateway.
- `execute_queries()`: Executes the queries at the specified frequencies and pushes the metrics to Prometheus.

## Note

This script is set to sleep for 30 seconds between each cycle of query execution. Adjust this interval as needed.

## License

This project is licensed under the MIT License.
