# Configure queries and execution frequencies

queries = {
    "95tile": {
        "query": 'SELECT "95tile" FROM "default.measurements.talon" WHERE ("region" =~ /^USS/ AND "latencyType" = "client.update.message.loadAndSend") AND time >= 1695907248642ms and time <= 1695916384594ms GROUP by "messageType"',
        "frequency": 900  # 900 seconds = 15 minutes        
    },
    "average": {
        "query": "SELECT mean(\"value\") AS \"average\" FROM measurements.gilgo",
        "frequency": 1800  # 1800 seconds = 30 minutes
    },
    "query1": {
        "query": "SELECT field1 FROM measurement1",
        "frequency": 300  # 300 seconds = 5 minutes
    },
    "query2": {
        "query": "SELECT field2 FROM measurement2",
        "frequency": 600  # 600 seconds = 10 minutes
    },
    "mean": {
        "query" : 'SELECT mean("usage") FROM "cpu" WHERE time >= now() - 1h GROUP BY time(10m)',
        "frequency": 1500
    },
    # Add more queries here...
}

flux_query = '''
f = (r) => 
  r._measurement == "measurement.Talon" and 
  r._field == "value" and 
  r.metricName == "external.release.response.time" and 
  r.operation == "create" and 
  r.region == "ASIA"

data = from(bucket: "two_weeks_only")
  |> range(start: -12h)
  |> filter(fn: f)

minQuery = data
  |> aggregateWindow(every: 15m, fn: min, createEmpty: false)

maxQuery = data
  |> aggregateWindow(every: 15m, fn: max, createEmpty: false)

avgQuery = data
  |> aggregateWindow(every: 15m, fn: mean, createEmpty: false)

p90Query = data
  |> aggregateWindow(every: 15m, fn: (tables=<-, column) => tables |> percentile(column: column, percentile: 0.9), createEmpty: false)

p95Query = data
  |> aggregateWindow(every: 15m, fn: (tables=<-, column) => tables |> percentile(column: column, percentile: 0.95), createEmpty: false)

union(tables: [minQuery, maxQuery, avgQuery, p90Query, p95Query])
'''