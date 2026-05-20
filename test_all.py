import requests
import time
import random

URL = "http://localhost:5000/add_data"

def run_master_test():
    print("🚀 Starting Master Test (Temp, Light, Energy + Alerts)")
    for i in range(1, 11):
        # Temp Alert > 30
        t_val = 24 + (i * 1.5)
        t_stat = "Alert" if t_val > 30 else "Normal"
        requests.post(URL, json={"sensor_id": "VIRT-001", "location": "Lab", "type": "temperature", "value": round(t_val, 2), "status": t_stat})

        # Light Alert < 300
        l_val = 500 - (i * 40)
        l_stat = "Alert" if l_val < 300 else "Normal"
        requests.post(URL, json={"sensor_id": "VIRT-002", "location": "Hall", "type": "light", "value": l_val, "status": l_stat})

        # Energy Alert > 40
        e_val = 20 + random.uniform(5, 30)
        if i == 7: e_val = 55.0
        e_stat = "Alert" if e_val > 40 else "Normal"
        requests.post(URL, json={"sensor_id": "VIRT-003", "location": "Office", "type": "energy", "value": round(e_val, 2), "status": e_stat})

        print(f"Round {i}: Data Sent.")
        time.sleep(1.5)

if __name__ == "__main__":
    run_master_test()
