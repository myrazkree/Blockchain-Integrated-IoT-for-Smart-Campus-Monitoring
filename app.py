import hashlib
import json
from time import time
from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
from sklearn.linear_model import LinearRegression

app = Flask(__name__)
CORS(app)

class Block:
    def __init__(self, index, data, previous_hash):
        self.index = index
        self.timestamp = time()
        self.data = data
        self.previous_hash = previous_hash
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash
        }, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]

    def create_genesis_block(self):
        return Block(0, "Genesis Block", "0")

    def get_latest_block(self):
        return self.chain[-1]

    def add_block(self, data):
        new_block = Block(len(self.chain), data, self.get_latest_block().hash)
        self.chain.append(new_block)

blockchain = Blockchain()

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if data.get("user") == "admin" and data.get("pass") == "1234":
        return {"status": "success"}
    return {"status": "fail"}

@app.route('/add_data', methods=['POST'])
def add_data():
    data = request.get_json()
    if data.get("status") == "Alert":
        data["alert_id"] = f"ALRT-{int(time())}"
    else:
        data["alert_id"] = "N/A"
    blockchain.add_block(data)
    return {"message": "Block added"}, 200

@app.route('/chain', methods=['GET'])
def get_chain():
    sensor_blocks = [b.data for b in blockchain.chain if isinstance(b.data, dict)]
    unique_sensors = len(set(d.get('sensor_id') for d in sensor_blocks if 'sensor_id' in d))
    active_alerts = len([d for d in sensor_blocks if d.get('status') == 'Alert'])
    return {
        "chain": [b.__dict__ for b in blockchain.chain],
        "total_sensors": unique_sensors,
        "active_alerts": active_alerts
    }

@app.route('/predict', methods=['GET'])
def predict():
    predictions = {}
    for t in ['temperature', 'light', 'energy']:
        values = [b.data['value'] for b in blockchain.chain if isinstance(b.data, dict) and b.data.get('type') == t]
        if len(values) < 5:
            predictions[t] = "Learning..."
        else:
            y = np.array(values)
            X = np.array(range(len(y))).reshape(-1, 1)
            model = LinearRegression().fit(X, y)
            next_val = model.predict([[len(y)]])[0]
            predictions[t] = round(float(next_val), 2)
    return jsonify(predictions)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
