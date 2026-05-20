import requests

# URL of your backend
URL = "http://localhost:5000/add_data"

# This data packet has status set to "Alert"
alert_packet = {
    "sensor_id": "VIRT-001",
    "location": "Virtual Lab",
    "type": "temperature",
    "value": 48.5,
    "status": "Alert"
}

response = requests.post(URL, json=alert_packet)

if response.status_code == 200:
    print("Successfully sent Alert! Refresh your logs.html to see the new ID.")
else:
    print("Failed to send alert.")
