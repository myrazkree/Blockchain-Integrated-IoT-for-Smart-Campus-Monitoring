# ==========================================================
# FILE INFORMATION
# ==========================================================
# File Name:
# app.py
#
# Project:
# Blockchain Integrated IoT System for Smart Campus Monitoring
#
# Developer:
# Nur Amira Najwa binti Zulkhibree
#
# Supervisor:
# Associate Professor Dr. Halikul bin Lenando
#
# Purpose:
# Provides administrator dashboard for monitoring
# IoT sensor data, blockchain records, alerts,
# AI predictions, and analytics visualization.
#
# Version:
# Final FYP Submission
#
# Last Updated:
# 10 June 2026
# ========================================================== 

# ==========================================================
# SYSTEM REQUIREMENTS
# ==========================================================
#
# Frontend:
# - HTML5
# - CSS3
# - JavaScript ES6
# - Chart.js
#
# Backend:
# - Python 3.x
# - Flask Framework
#
# Database:
# SQLite
#
# Machine Learning:
# - Scikit-Learn
#
# Hardware:
# - ESP32
# - DHT22
# - BH1750
# - PZEM-004T
#
# ==========================================================

# ==========================================================
# IMPORT REQUIRED LIBRARIES
# ==========================================================
# hashlib         -> Generates SHA-256 cryptographic hashes
# json            -> Converts data structures into JSON strings
# time            -> Generates timestamps for blockchain records
# Flask           -> Web framework for API and dashboard
# CORS            -> Allows ESP32 and frontend communication
# NumPy           -> Data processing for AI prediction
# LinearRegression-> Machine learning model for forecasting
# SQLAlchemy      -> Database ORM for SQLite interaction
# ==========================================================

import hashlib
import json
from time import time
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import numpy as np
from sklearn.linear_model import LinearRegression
from flask_sqlalchemy import SQLAlchemy

# ==========================================================
# APPLICATION INITIALIZATION
# ==========================================================
# Creates Flask web application and enables
# cross-origin communication between frontend,
# ESP32 IoT nodes and backend services.
# ==========================================================

app = Flask(__name__)
CORS(app)

# Configure SQLite database location
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////home/amirazkree/smartcampus/campus.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ==========================================================
# SENSOR DATA TABLE
# ==========================================================
# Stores:
# - Sensor information
# - Sensor readings
# - Blockchain hashes
# - Blockchain links between blocks
#
# current_hash  -> SHA-256 hash generated from block contents
# previous_hash -> Stores parent block hash to create blockchain linkage
# ==========================================================

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

# ==========================================================
# DASHBOARD PAGE
# ==========================================================
# Loads the main Smart Campus dashboard
# showing sensor values, AI predictions
# and analytics charts.
# ==========================================================

@app.route('/')
def home():
    return render_template("index.html")

# ==========================================================
# BLOCKCHAIN LEDGER PAGE
# ==========================================================
# Displays all blockchain records together
# with their integrity validation status.
# ==========================================================

@app.route('/logs')
def logs():
    return render_template("logs.html")

# ==========================================================
# ADMIN AUTHENTICATION
# ==========================================================
# Validates administrator username
# and password before allowing
# dashboard access.
# ==========================================================

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if data.get("user") == "admin" and data.get("pass") == "MiraSecure2026!":
        return jsonify({"status": "success"})
    return jsonify({"status": "fail"})

# ==========================================================
# BLOCK CREATION AND DATA INGESTION
# ==========================================================
# Purpose:
# 1. Receive sensor data from ESP32 nodes.
# 2. Generate alert IDs when thresholds are exceeded.
# 3. Retrieve previous block hash.
# 4. Build blockchain payload.
# 5. Generate SHA-256 hash.
# 6. Store block and hashes permanently in SQLite.
#
# Each sensor reading becomes a blockchain block.
# ==========================================================

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

# Retrieve latest block from database.
# This block becomes the parent of the new block.
# Blockchain continuity is maintained using
# previous_hash references.

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

# Generate unique SHA-256 fingerprint.
# Any change in block contents produces
# a completely different hash value.

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

# ==========================================================
# BLOCKCHAIN SYNCHRONIZATION SERVICE
# ==========================================================
# Purpose:
# 1. Retrieve all stored blocks.
# 2. Recalculate hashes at runtime.
# 3. Verify blockchain integrity.
# 4. Detect tampering attempts.
# 5. Return chain to dashboard.
# ==========================================================

@app.route('/chain', methods=['GET'])
def chain():
    unique_sensors = db.session.query(SensorData.sensor_id).distinct().count()
    active_alerts = SensorData.query.filter_by(status='Alert').count()

# Genesis Block:
# The first block in the blockchain.
# It has no parent block and acts
# as the starting reference point
# for the entire chain.

    synchronized_chain = [{
        "index": 0,
        "timestamp": 1779466552.4295905,
        "data": "Genesis Block",
        "previous_hash": "0",
        "hash": "B2282d6c00dc5a4319b71f71723c748d6bbc14fb1c3a10cf8fca25510051",
        "integrity_status": "VALID"
    }]

    try:
        db_records = SensorData.query.order_by(SensorData.id.asc()).all()

        # Track the expected previous hash as we iterate to check for pointer breaks
        expected_prev_hash = "B2282d6c00dc5a4319b71f71723c748d6bbc14fb1c3a10cf8fca25510051"

        for idx, record in enumerate(db_records, start=1):
            payload = {
                "sensor_id": record.sensor_id,
                "location": record.location,
                "type": record.type,
                "value": record.value,
                "status": record.status,
                "alert_id": f"ALRT-{int(record.timestamp)}" if record.status == "Alert" else "N/A"
            }

            # RE-COMPUTE THE RUNTIME HASH EXACTLY LIKE THE INGESTION TIER DOES
            block_string = json.dumps({
                "index": idx,
                "timestamp": record.timestamp,
                "data": payload,
                "previous_hash": record.previous_hash
            }, sort_keys=True).encode()

            recomputed_runtime_hash = hashlib.sha256(block_string).hexdigest()

            # INTEGRITY CHECK LOGIC (Matches Table 5.3.2.1)
            integrity_status = "VALID"

# ==========================================================
# BLOCKCHAIN INTEGRITY VERIFICATION
# ==========================================================
#
# Check 1:
# Recompute block hash and compare
# against stored hash.
#
# Result:
# CHAIN BROKEN
#
# Check 2:
# Verify previous_hash correctly
# references parent block hash.
#
# Result:
# INVALID PARENT
#
# If both checks pass:
# VALID
# ==========================================================

            # Check 1: Did the current block data change? (Triggers CHAIN BROKEN)
            # Runtime hash is recalculated and compared
            # against the stored hash. If they differ,
            # the block data has been modified after storage.
            if recomputed_runtime_hash != record.current_hash:
                integrity_status = "CHAIN BROKEN"

            # Check 2: Did the previous block break, corrupting this block's link? (Triggers INVALID PARENT)
            elif record.previous_hash != expected_prev_hash:
                integrity_status = "INVALID PARENT"

            synchronized_chain.append({
                "index": idx,
                "timestamp": record.timestamp,
                "data": payload,
                "previous_hash": record.previous_hash,
                "saved_hash": record.current_hash,
                "runtime_hash": recomputed_runtime_hash,
                "integrity_status": integrity_status
            })

            # Pass the authentic saved hash onward to validate the next block link pointer
            expected_prev_hash = record.current_hash

    except Exception as e:
        print(f"Sync error parsing SQL to Block Array: {e}")

    return jsonify({
        "chain": synchronized_chain,
        "total_sensors": unique_sensors,
        "active_alerts": active_alerts
    })

# ==========================================================
# AI FORECASTING ENGINE
# ==========================================================
# Uses Linear Regression to learn
# trends from historical sensor data
# and estimate the next expected value.
#
# Sensor Types:
# - Temperature
# - Light
# - Energy
# ==========================================================

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

# Train linear regression model
# using historical blockchain data
# and forecast the next expected value.

                model = LinearRegression()
                model.fit(X, y)

                next_val = model.predict([[len(y)]])[0]
                predictions[t] = round(float(next_val), 2)

        except Exception as e:
            predictions[t] = "Error"

    return jsonify(predictions)

# ==========================================================
# ENERGY SENSOR SIMULATION
# ==========================================================
# Generates sample energy readings
# for testing AI prediction and
# blockchain functionality when
# physical sensor hardware is unavailable.
# ==========================================================

@app.route('/simulate_energy')
def simulate_energy():

    sample_values = [4.9, 4.9, 4.9, 4.9, 4.8, 4.8, 4.8, 4.9, 4.9, 4.8]

    for val in sample_values:

        current_time = time()

        last_record = SensorData.query.order_by(SensorData.id.desc()).first()

        if last_record:
            prev_hash = last_record.current_hash
            next_idx = last_record.id + 1
        else:
            prev_hash = "0"
            next_idx = 1

# Create blockchain payload containing
# sensor information and monitoring results.
# This data will be digitally signed
# using SHA-256 hashing.

        payload = {
            "sensor_id": "S003",
            "location": "Block C",
            "type": "energy",
            "value": val,
            "status": "Normal",
            "alert_id": "N/A"
        }

        block_string = json.dumps({
            "index": next_idx,
            "timestamp": current_time,
            "data": payload,
            "previous_hash": prev_hash
        }, sort_keys=True).encode()

# Generate SHA-256 cryptographic signature.
#
# Any modification to:
# - sensor value
# - timestamp
# - sensor ID
# - previous hash
#
# will produce a completely different hash,
# allowing tampering detection.

        calculated_hash = hashlib.sha256(block_string).hexdigest()

# Save blockchain block into database
# together with its cryptographic hash
# and link to the previous block.

        new_data = SensorData(
            sensor_id="S003",
            location="Block C",
            type="energy",
            value=val,
            status="Normal",
            timestamp=current_time,
            current_hash=calculated_hash,
            previous_hash=prev_hash
        )

        db.session.add(new_data)

    db.session.commit()

    return jsonify({
        "message": "Energy simulation inserted into blockchain"
    })

# ---------------- STARTUP ----------------
# Automatically creates database tables
# during application startup if they
# do not already exist.
with app.app_context():
    db.create_all()


# ---------------- RUN ----------------
# ==========================================================
# APPLICATION ENTRY POINT
# ==========================================================
# Starts Flask web server and exposes
# blockchain APIs, dashboard pages
# and AI prediction services.
# ==========================================================

if __name__ == "__main__":
    app.run()

# ==========================================================
# FUTURE ENHANCEMENTS
# ==========================================================
#
# 1. Blockchain consensus validation.
# 2. Multi-user authentication.
# 3. Role-based access control.
# 4. AI anomaly detection.
# 5. Cloud deployment support.
# 6. MQTT integration.
# 7. Mobile application dashboard.
# 8. Real-time push notifications.
#
# ========================================================== 

# ==========================================================
# ACADEMIC CONTRIBUTION
# ==========================================================
#
# This dashboard demonstrates the
# integration of:
# 
# 1. Internet of Things (IoT)
# 2. Blockchain Technology
# 3. Artificial Intelligence
# 4. Web-Based Monitoring Systems
# 
# to provide secure and intelligent
# Smart Campus monitoring.
#
# ========================================================== -

# ==========================================================
# COPYRIGHT NOTICE
# ==========================================================
#
# © 2026 Nur Amira Najwa binti Zulkhibree
#
# This source code was developed for
# academic purposes under the project:
#
# "Blockchain Integrated IoT System for
# Smart Campus Monitoring"
#
# Faculty of Computer Science and Information Technology
# Universiti Malaysia Sarawak (UNIMAS)
#
# ========================================================== 
