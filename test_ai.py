import requests
import time
import random

# The URL of your running app.py
URL = "http://localhost:5000/add_data"

def send_mock_data():
    print("Starting Virtual Sensor Test... (Sending 10 rounds of data)")
    
    for i in range(1, 11):
        # 1. Simulate Temperature (Increasing trend to test AI prediction)
        temp_val = 20 + i + random.uniform(-0.5, 0.5)
        requests.post(URL, json={
            "sensor_id": "VIRT-001",
            "location": "Virtual Lab",
            "type": "temperature",
            "value": round(temp_val, 2),
            "status": "Normal"
        })

        # 2. Simulate Light (Steady trend)
        light_val = 500 + random.randint(-10, 10)
        requests.post(URL, json={
            "sensor_id": "VIRT-002",
            "location": "Virtual Hall",
            "type": "light",
            "value": light_val,
            "status": "Normal"
        })

        # 3. Simulate Energy (Random spikes)
        energy_val = random.uniform(10, 50)
        requests.post(URL, json={
            "sensor_id": "VIRT-003",
            "location": "Virtual Office",
            "type": "energy",
            "value": round(energy_val, 2),
            "status": "Normal"
        })

        print(f"Round {i}: Data sent to Blockchain.")
        time.sleep(1) # Send data every second for fast testing

    print("\nTest Complete! Refresh your Dashboard now.")

if __name__ == "__main__":
    send_mock_data()
