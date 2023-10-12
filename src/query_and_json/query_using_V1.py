import requests

# Set the URL and token for the InfluxDB API
url = "https://your-influxdb-url.com"
token = "your-influxdb-token"

# Set the headers for the request
headers = {
    "Authorization": f"Token {token}",
    "Content-Type": "application/json"
}

# Set the payload for the request
payload = {
    "query": "SELECT * FROM my_measurement"
}

# Send the request to the InfluxDB API
response = requests.post(url, headers=headers, json=payload)

# Check the response status code
if response.status_code == 200:
    # Parse the JSON response
    data = response.json()
    print(data)
else:
    print("Error:", response.text)