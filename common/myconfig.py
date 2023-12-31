import os

# Set default values for the variables
host = os.environ.get('HOST', 'localhost')
port = int(os.environ.get('PORT', '18086'))
username = os.environ.get('USERNAME', 'your_username')
password = os.environ.get('PASSWORD', 'your_password')
org = os.environ.get('DATABASE', 'your_database')
url = os.environ.get('INFLUXURL', 'https://localhost:18086/')
token = os.environ.get('INFLUX_TOKEN', '')
# To create secure connections
ssl = os.environ.get('INFLUXDB_SSL', True)
verify_ssl = os.environ.get('INFLUXDB_VERIFY_SSL', True)
os.environ['REQUESTS_CA_BUNDLE'] = 'PATH' # The actual absolute .pem file path

prometheus_pushgateway_url = os.environ.get('PROMETHEUS_PUSHGATEWAY_URL', 'http://localhost:9091/metrics/job/my_job')
prometheusport = int(os.environ.get('PROMETHEUS_PORT', '8080'))




