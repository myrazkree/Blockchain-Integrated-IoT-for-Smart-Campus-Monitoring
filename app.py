import hashlib
import json
from time import time
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import numpy as np
from sklearn.linear_model import LinearRegression
from flask_sqlalchemy import SQLAlchemy

# ---------------- APP SETUP ----------------
app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////home/amirazkree/smartcampus/campus.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ---------------- DATABASE ----------------
# FIXED: Added dedicated columns to store blockchain hashes permanently
class SensorData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sensor_id = db.Column(db.String(50))
    location = db.Column(db.String(50))
    type = db.Column(db.String(50))
    value = db.Column(db.Float)
    status = db.Column(db.String(20))
    timestamp = db.Column(db.Float)
    current_hash = db.Column(db.String(64))   # Stores the SHA-256 string
    previous_hash = db.Column(db.String(64))  # Links to the block before it

# ---------------- ROUTES ----------------

@app.route('/')
def home():
    return render_template("index.html")


@app.route('/logs')
def logs():
    return render_template("logs.html")


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if data.get("user") == "admin" and data.get("pass") == "MiraSecure2026!":
        return jsonify({"status": "success"})
    return jsonify({"status": "fail"})


@app.route('/add_data', methods=['POST'])
def add_data():
    data = request.get_json(force=True, silent=True)

    if not data:
        return jsonify({"error": "No JSON payload received"}), 400

    current_time = time()

    if data.get("status") == "Alert":
        data["alert_id"] = f"ALRT-{int(current_time)}"
    else:
        data["alert_id"] = "N/A"

    try:
        sensor_value = float(data.get("value", 0.0))
    except (ValueError, TypeError):
        sensor_value = 0.0

    # 1. FIXED: Look up the last entry written to the database to find the parent hash
    last_record = SensorData.query.order_by(SensorData.id.desc()).first()
    
    if last_record:
        prev_hash = last_record.current_hash
        next_idx = last_record.id + 1
    else:
        # If database is blank, link to a hardcoded Genesis block hash anchor
        prev_hash = "0"
        next_idx = 1

    # 2. FIXED: Construct the block payload data string and hash it BEFORE writing to SQLite
    payload = {
        "sensor_id": data.get("sensor_id"),
        "location": data.get("location"),
        "type": data.get("type"),
        "value": sensor_value,
        "status": data.get("status", "Normal"),
        "alert_id": data["alert_id"]
    }

    block_string = json.dumps({
        "index": next_idx,
        "timestamp": current_time,
        "data": payload,
        "previous_hash": prev_hash
    }, sort_keys=True).encode()

    calculated_hash = hashlib.sha256(block_string).hexdigest()

    # 3. FIXED: Store all raw metrics alongside the actual cryptographic signature hashes
    new_data = SensorData(
        sensor_id=data.get("sensor_id"),
        location=data.get("location"),
        type=data.get("type"),
        value=sensor_value,
        status=data.get("status", "Normal"),
        timestamp=current_time,
        current_hash=calculated_hash,
        previous_hash=prev_hash
    )

    db.session.add(new_data)
    db.session.commit()

    return jsonify({"message": "Data saved securely inside block ledger", "hash": calculated_hash}), 200


@app.route('/chain', methods=['GET'])
def chain():
    unique_sensors = db.session.query(SensorData.sensor_id).distinct().count()
    active_alerts = SensorData.query.filter_by(status='Alert').count()

    # Base anchor point initialization
    synchronized_chain = [{
        "index": 0,
        "timestamp": 1779466552.4295905, 
        "data": "Genesis Block",
        "previous_hash": "0",
        "hash": "B2282d6c00dc5a4319b71f71723c748d6bbc14fb1c3a10cf8fca25510051"
    }]

    try:
        db_records = SensorData.query.order_by(SensorData.id.asc()).all()

        for idx, record in enumerate(db_records, start=1):
            payload = {
                "sensor_id": record.sensor_id,
                "location": record.location,
                "type": record.type,
                "value": record.value,
                "status": record.status,
                "alert_id": f"ALRT-{int(record.timestamp)}" if record.status == "Alert" else "N/A"
            }

            # FIXED: Instead of calculating blindly, we now pull the authentic historical hashes saved right from the database
            synchronized_chain.append({
                "index": idx,
                "timestamp": record.timestamp,
                "data": payload,
                "previous_hash": record.previous_hash,
                "hash": record.current_hash
            })

    except Exception as e:
        print(f"Sync error parsing SQL to Block Array: {e}")

    return jsonify({
        "chain": synchronized_chain,
        "total_sensors": unique_sensors,
        "active_alerts": active_alerts
    })


@app.route('/predict', methods=['GET'])
def predict():
    predictions = {}

    for t in ['temperature', 'light', 'energy']:
        records = SensorData.query.filter_by(type=t).order_by(SensorData.id.asc()).all()
        values = [r.value for r in records if r.value is not None]

        try:
            if len(values) < 5:
                predictions[t] = "Learning..."
            else:
                y = np.array(values)
                X = np.array(range(len(y))).reshape(-1, 1)

                model = LinearRegression()
                model.fit(X, y)

                next_val = model.predict([[len(y)]])[0]
                predictions[t] = round(float(next_val), 2)

        except Exception as e:
            predictions[t] = "Error"

    return jsonify(predictions)


# ---------------- STARTUP ----------------
with app.app_context():
    db.create_all()


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run()
