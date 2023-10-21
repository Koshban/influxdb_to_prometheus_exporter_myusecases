# Flask Application with InfluxDB and Prometheus

This Project queries influxDB and Posts data for Prometheus scraper to read. It has been built in 2 ways :

- Flask web application that interacts with InfluxDB and Prometheus to execute queries, log results, and expose metrics.

- FastAPI application that periodically executes queries on an InfluxDB database, logs the results, sends the data to a specified endpoint, and updates Prometheus metrics. It also exposes endpoints to get and post these metrics.

## Features

Configurable SSL for HTTPS.
Logging of the application activity to a log file.
Execution of InfluxDB queries and logging of the results.
Scheduling of tasks to periodically execute these queries.
Sending the data to a specific endpoint.
Updating Prometheus metrics.
Endpoints to get and post these metrics.

## Getting Started

To get the application running, you need to have Flask, InfluxDB, and Prometheus installed on your system.

### Prerequisites

- Flask
- InfluxDBClient
- Prometheus_client
- Pandas
- FASTAPI
- SSL Certificates : Place your SSL certificate and key in the path specified in the script

### Installation

```bash
git clone https://github.com/your-repository/koshban-trading-metrics-service.git
pip install -r requirements.txt
``````

Place your SSL certificate and key in the path specified in the script.

Configure InfluxDB connection details in common/connections.py file.

Configure the queries to be executed on InfluxDB in common/influxqueries.py file.

Configure various environmental details in common/myconfig.py or add in the .profile of the user account that will run the App.

### Endpoints

GET /koshban-trading-metrics - Get the latest metrics.
POST /koshban-trading-metrics - Post metrics data.

### Usage

This application has two main routes:

/start: starts worker threads that execute InfluxDB queries and update Prometheus metrics.
/koshban-trading-metrics: returns Prometheus metrics in text format for GET requests and prints POSTed data for POST requests.

## License

This project is licensed under the MIT License.
