import os

base_dir = r"E:\COLLEGE\sem 3\Projects\AIOT\Traffic_Flow_Prediction"

files = {
    "requirements.txt": """flask
opencv-python
numpy
pandas
scikit-learn
joblib
""",
    "README.md": """# Traffic Flow Prediction Using Camera + Sensor Data

A prototype intelligent traffic-monitoring system that combines camera/video input for vehicle detection with simulated sensor data to predict traffic flow and congestion using Machine Learning.

## Features
- Vehicle detection and tracking from video
- Vehicle counting by type (Car, Bike, Bus, Truck)
- Sensor data simulation
- Data fusion (Camera + Sensor)
- Machine Learning for traffic prediction (Random Forest)
- Web dashboard for real-time monitoring

## Architecture
Video -> OpenCV -> Vehicle Detection & Tracking -> Feature Extraction
                                                     |
Sensor Simulator ------------------------------------+
                                                     |
                                                Data Fusion
                                                     |
                                                ML Prediction
                                                     |
                                                  SQLite
                                                     |
                                                 Flask API
                                                     |
                                                Dashboard

## Installation

1. Create a virtual environment:
   `python -m venv venv`
2. Activate the virtual environment:
   Windows: `venv\\Scripts\\activate`
   Linux/macOS: `source venv/bin/activate`
3. Install dependencies:
   `pip install -r requirements.txt`

## Preparation

1. Generate simulated dataset and synthetic video:
   `python data/generate_data.py`
2. Train the Machine Learning models:
   `python -m ml.train`
3. Initialize Database:
   The database will be automatically initialized when running `app.py`.

## Running the application

1. Start the Flask application:
   `python app.py`
2. Open your browser and navigate to:
   `http://127.0.0.1:5000`
3. Click "Start Demo" on the dashboard to begin processing the video and simulated data.
""",
    ".gitignore": """__pycache__/
*.py[cod]
*$py.class
venv/
*.db
*.pkl
""",
    "data/generate_data.py": """import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import cv2
import os

def generate_historical_data():
    np.random.seed(42)
    end_time = datetime.now()
    start_time = end_time - timedelta(days=30)
    
    timestamps = pd.date_range(start=start_time, end=end_time, freq='10min')
    
    traffic_data = []
    sensor_data = []
    
    for t in timestamps:
        hour = t.hour
        if 7 <= hour <= 9 or 16 <= hour <= 19:
            base_count = np.random.randint(50, 100)
            density = np.random.uniform(60, 95)
            speed = np.random.uniform(10, 30)
        elif 0 <= hour <= 5:
            base_count = np.random.randint(5, 20)
            density = np.random.uniform(5, 20)
            speed = np.random.uniform(50, 80)
        else:
            base_count = np.random.randint(20, 60)
            density = np.random.uniform(20, 60)
            speed = np.random.uniform(30, 60)
            
        cars = int(base_count * 0.6)
        bikes = int(base_count * 0.25)
        buses = int(base_count * 0.05)
        trucks = base_count - cars - bikes - buses
        
        traffic_data.append([t, base_count, cars, bikes, buses, trucks, speed, density])
        sensor_data.append([t, 'sensor_1', base_count + np.random.randint(-5, 6), speed + np.random.uniform(-5, 5), density + np.random.uniform(-2, 2)])
        
    df_traffic = pd.DataFrame(traffic_data, columns=['timestamp', 'vehicle_count', 'car_count', 'bike_count', 'bus_count', 'truck_count', 'average_speed', 'occupancy'])
    df_traffic['traffic_density'] = df_traffic['occupancy']
    os.makedirs('data/raw', exist_ok=True)
    df_traffic.to_csv('data/raw/traffic.csv', index=False)
    
    df_sensor = pd.DataFrame(sensor_data, columns=['timestamp', 'sensor_name', 'vehicle_count', 'average_speed', 'occupancy'])
    df_sensor['traffic_density'] = df_sensor['occupancy']
    df_sensor.to_csv('data/raw/sensors.csv', index=False)
    print("Historical data generated.")

def generate_synthetic_video(output_path='data/videos/traffic.mp4', frames=300, width=640, height=480):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, 30.0, (width, height))
    
    cars = [
        [0, 200, 60, 40, 5, (255, 0, 0), "car"],
        [640, 300, 80, 50, -4, (0, 0, 255), "bus"],
        [0, 150, 40, 20, 7, (0, 255, 0), "bike"]
    ]
    
    for _ in range(frames):
        frame = np.ones((height, width, 3), dtype=np.uint8) * 100 
        cv2.line(frame, (0, 240), (640, 240), (255, 255, 255), 2)
        
        for car in cars:
            x, y, w, h, s, c, t = car
            cv2.rectangle(frame, (int(x), int(y)), (int(x+w), int(y+h)), c, -1)
            car[0] += s
            if car[0] > width + 100:
                car[0] = -100
            elif car[0] < -100:
                car[0] = width + 100
                
        out.write(frame)
        
    out.release()
    print(f"Generated synthetic video at {output_path}")

if __name__ == '__main__':
    generate_historical_data()
    generate_synthetic_video()
""",
    "database/schema.sql": """
CREATE TABLE IF NOT EXISTS traffic_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    vehicle_count INTEGER,
    car_count INTEGER,
    bike_count INTEGER,
    bus_count INTEGER,
    truck_count INTEGER,
    average_speed REAL,
    occupancy REAL,
    traffic_density REAL
);

CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    predicted_vehicle_count INTEGER,
    predicted_density REAL,
    congestion_level TEXT,
    prediction_horizon TEXT
);

CREATE TABLE IF NOT EXISTS sensor_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    sensor_name TEXT,
    vehicle_count INTEGER,
    average_speed REAL,
    occupancy REAL,
    traffic_density REAL
);
""",
    "ml/__init__.py": "",
    "ml/preprocess.py": """import pandas as pd
import numpy as np

def preprocess_data(traffic_df, sensor_df=None):
    if sensor_df is not None:
        df = pd.merge(traffic_df, sensor_df[['timestamp', 'vehicle_count', 'average_speed']], on='timestamp', suffixes=('', '_sensor'))
        df['vehicle_count'] = df[['vehicle_count', 'vehicle_count_sensor']].mean(axis=1).astype(int)
        df['average_speed'] = df[['average_speed', 'average_speed_sensor']].mean(axis=1)
        df.drop(columns=['vehicle_count_sensor', 'average_speed_sensor'], inplace=True)
    else:
        df = traffic_df.copy()
        
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['hour'] = df['timestamp'].dt.hour
    df['minute'] = df['timestamp'].dt.minute
    df['day_of_week'] = df['timestamp'].dt.dayofweek
    df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
    df['peak_hour'] = df['hour'].isin([7, 8, 9, 16, 17, 18, 19]).astype(int)
    
    return df

def extract_features(df):
    features = ['car_count', 'bike_count', 'bus_count', 'truck_count', 'average_speed', 'occupancy', 'hour', 'day_of_week', 'is_weekend', 'peak_hour']
    
    df['future_vehicle_count'] = df['vehicle_count'].shift(-1)
    df['future_density'] = df['traffic_density'].shift(-1)
    
    df = df.dropna()
    X = df[features]
    
    y_reg = df['future_vehicle_count']
    
    def get_congestion(density):
        if density <= 35: return 0 # LOW
        if density <= 70: return 1 # MEDIUM
        return 2 # HIGH
        
    y_clf = df['future_density'].apply(get_congestion)
    
    return X, y_reg, y_clf
""",
    "ml/train.py": """import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, accuracy_score, precision_score, recall_score, f1_score
import joblib
import json
import os
from ml.preprocess import preprocess_data, extract_features

def train_models():
    traffic_df = pd.read_csv('data/raw/traffic.csv')
    sensor_df = pd.read_csv('data/raw/sensors.csv')
    
    df = preprocess_data(traffic_df, sensor_df)
    X, y_reg, y_clf = extract_features(df)
    
    X_train, X_test, y_reg_train, y_reg_test, y_clf_train, y_clf_test = train_test_split(
        X, y_reg, y_clf, test_size=0.2, random_state=42
    )
    
    reg_model = RandomForestRegressor(n_estimators=50, random_state=42)
    reg_model.fit(X_train, y_reg_train)
    reg_preds = reg_model.predict(X_test)
    
    clf_model = RandomForestClassifier(n_estimators=50, random_state=42)
    clf_model.fit(X_train, y_clf_train)
    clf_preds = clf_model.predict(X_test)
    
    metrics = {
        "regression": {
            "mae": round(mean_absolute_error(y_reg_test, reg_preds), 2),
            "rmse": round(mean_squared_error(y_reg_test, reg_preds, squared=False), 2),
            "r2": round(r2_score(y_reg_test, reg_preds), 2)
        },
        "classification": {
            "accuracy": round(accuracy_score(y_clf_test, clf_preds), 2),
            "precision": round(precision_score(y_clf_test, clf_preds, average='weighted', zero_division=0), 2),
            "recall": round(recall_score(y_clf_test, clf_preds, average='weighted', zero_division=0), 2),
            "f1": round(f1_score(y_clf_test, clf_preds, average='weighted', zero_division=0), 2)
        }
    }
    
    os.makedirs('ml', exist_ok=True)
    joblib.dump(reg_model, 'ml/flow_model.pkl')
    joblib.dump(clf_model, 'ml/congestion_model.pkl')
    
    with open('ml/metadata.json', 'w') as f:
        json.dump(metrics, f, indent=4)
        
    print("Models trained and saved successfully.")
    print("Metrics:", metrics)

if __name__ == '__main__':
    train_models()
""",
    "ml/predict.py": """import joblib
import pandas as pd
from datetime import datetime
import os

class Predictor:
    def __init__(self):
        self.flow_model = None
        self.congestion_model = None
        self._load_models()
        
    def _load_models(self):
        if os.path.exists('ml/flow_model.pkl') and os.path.exists('ml/congestion_model.pkl'):
            self.flow_model = joblib.load('ml/flow_model.pkl')
            self.congestion_model = joblib.load('ml/congestion_model.pkl')
            
    def predict(self, fused_data):
        if not self.flow_model or not self.congestion_model:
            return None
            
        now = datetime.now()
        features = {
            'car_count': [fused_data.get('car_count', 0)],
            'bike_count': [fused_data.get('bike_count', 0)],
            'bus_count': [fused_data.get('bus_count', 0)],
            'truck_count': [fused_data.get('truck_count', 0)],
            'average_speed': [fused_data.get('average_speed', 30.0)],
            'occupancy': [fused_data.get('occupancy', 50.0)],
            'hour': [now.hour],
            'day_of_week': [now.weekday()],
            'is_weekend': [1 if now.weekday() >= 5 else 0],
            'peak_hour': [1 if now.hour in [7,8,9,16,17,18,19] else 0]
        }
        
        df = pd.DataFrame(features)
        
        flow_pred = self.flow_model.predict(df)[0]
        congestion_pred = self.congestion_model.predict(df)[0]
        
        congestion_map = {0: "LOW", 1: "MEDIUM", 2: "HIGH"}
        
        return {
            "predicted_vehicle_count": int(flow_pred),
            "predicted_density": round(flow_pred * 0.8, 2),
            "congestion_level": congestion_map.get(congestion_pred, "UNKNOWN"),
            "prediction_horizon": "10 minutes"
        }
""",
    "camera/__init__.py": "",
    "camera/detector.py": """import cv2

class VehicleDetector:
    def __init__(self):
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=100, varThreshold=50, detectShadows=True)
        
    def detect(self, frame):
        fg_mask = self.bg_subtractor.apply(frame)
        _, fg_mask = cv2.threshold(fg_mask, 200, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        detections = []
        for contour in contours:
            if cv2.contourArea(contour) > 200:
                x, y, w, h = cv2.boundingRect(contour)
                area = w * h
                v_type = "car"
                if area < 1000:
                    v_type = "bike"
                elif area > 3500:
                    v_type = "bus"
                    
                detections.append({
                    "type": v_type,
                    "x1": x, "y1": y,
                    "x2": x + w, "y2": y + h,
                    "confidence": 0.90,
                    "centroid": (x + w//2, y + h//2)
                })
        return detections
""",
    "camera/tracker.py": """import math

class VehicleTracker:
    def __init__(self):
        self.tracked_vehicles = {}
        self.next_id = 0
        
    def update(self, detections):
        updated_vehicles = {}
        
        for det in detections:
            cx, cy = det["centroid"]
            matched_id = None
            
            for v_id, v_data in self.tracked_vehicles.items():
                px, py = v_data["centroid"]
                distance = math.hypot(cx - px, cy - py)
                
                if distance < 50:
                    matched_id = v_id
                    break
                    
            if matched_id is not None:
                updated_vehicles[matched_id] = {
                    "centroid": (cx, cy),
                    "type": det["type"],
                    "history": self.tracked_vehicles[matched_id]["history"] + [(cx, cy)]
                }
                del self.tracked_vehicles[matched_id]
            else:
                updated_vehicles[self.next_id] = {
                    "centroid": (cx, cy),
                    "type": det["type"],
                    "history": [(cx, cy)]
                }
                self.next_id += 1
                
        self.tracked_vehicles = updated_vehicles
        return self.tracked_vehicles
""",
    "camera/vehicle_counter.py": """class VehicleCounter:
    def __init__(self, counting_line_y=240):
        self.counting_line_y = counting_line_y
        self.counted_ids = set()
        self.counts = {
            "car_count": 0,
            "bike_count": 0,
            "bus_count": 0,
            "truck_count": 0,
            "total_count": 0
        }
        
    def update_counts(self, tracked_vehicles):
        for v_id, v_data in tracked_vehicles.items():
            if v_id in self.counted_ids:
                continue
                
            history = v_data["history"]
            if len(history) < 2:
                continue
                
            prev_y = history[-2][1]
            curr_y = history[-1][1]
            
            if (prev_y < self.counting_line_y and curr_y >= self.counting_line_y) or \
               (prev_y > self.counting_line_y and curr_y <= self.counting_line_y):
                self.counted_ids.add(v_id)
                self.counts["total_count"] += 1
                v_type = v_data["type"]
                if v_type == "car": self.counts["car_count"] += 1
                elif v_type == "bike": self.counts["bike_count"] += 1
                elif v_type == "bus": self.counts["bus_count"] += 1
                elif v_type == "truck": self.counts["truck_count"] += 1
                
        return self.counts
""",
    "camera/speed_estimator.py": """import math

class SpeedEstimator:
    def __init__(self, fps=30, pixels_per_meter=10):
        self.fps = fps
        self.pixels_per_meter = pixels_per_meter
        
    def estimate_speeds(self, tracked_vehicles):
        speeds = []
        for v_id, v_data in tracked_vehicles.items():
            history = v_data["history"]
            if len(history) > 5:
                dx = history[-1][0] - history[-5][0]
                dy = history[-1][1] - history[-5][1]
                distance_pixels = math.hypot(dx, dy)
                distance_meters = distance_pixels / self.pixels_per_meter
                time_seconds = 5 / self.fps
                speed_mps = distance_meters / time_seconds
                speed_kmh = speed_mps * 3.6
                speeds.append(speed_kmh)
                
        avg_speed = sum(speeds) / len(speeds) if speeds else 30.0
        return {"average_speed": round(avg_speed, 2)}
""",
    "sensors/__init__.py": "",
    "sensors/simulator.py": """import random
from datetime import datetime

class SensorSimulator:
    def get_latest_reading(self):
        base_count = random.randint(20, 80)
        return {
            "timestamp": datetime.now().isoformat(),
            "sensor_name": "sim_sensor_1",
            "vehicle_count": base_count,
            "average_speed": round(random.uniform(20.0, 60.0), 2),
            "occupancy": round(random.uniform(10.0, 80.0), 2),
            "traffic_density": round(random.uniform(15.0, 85.0), 2)
        }
""",
    "services/__init__.py": "",
    "services/data_service.py": """import sqlite3
from datetime import datetime
import os

DB_PATH = 'database/traffic.db'

def get_db_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        with open('database/schema.sql', 'r') as f:
            conn.executescript(f.read())

def insert_traffic_record(data):
    with get_db_connection() as conn:
        conn.execute('''
            INSERT INTO traffic_records 
            (vehicle_count, car_count, bike_count, bus_count, truck_count, average_speed, occupancy, traffic_density)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('vehicle_count', 0), data.get('car_count', 0), data.get('bike_count', 0),
            data.get('bus_count', 0), data.get('truck_count', 0), data.get('average_speed', 0.0),
            data.get('occupancy', 0.0), data.get('traffic_density', 0.0)
        ))
        
def insert_prediction(data):
    with get_db_connection() as conn:
        conn.execute('''
            INSERT INTO predictions 
            (predicted_vehicle_count, predicted_density, congestion_level, prediction_horizon)
            VALUES (?, ?, ?, ?)
        ''', (
            data.get('predicted_vehicle_count', 0), data.get('predicted_density', 0.0),
            data.get('congestion_level', 'UNKNOWN'), data.get('prediction_horizon', '10 minutes')
        ))

def get_latest_traffic():
    with get_db_connection() as conn:
        row = conn.execute('SELECT * FROM traffic_records ORDER BY id DESC LIMIT 1').fetchone()
        return dict(row) if row else None

def get_traffic_history(limit=20):
    with get_db_connection() as conn:
        rows = conn.execute('SELECT * FROM traffic_records ORDER BY id DESC LIMIT ?', (limit,)).fetchall()
        return [dict(row) for row in reversed(rows)]
        
def get_latest_prediction():
    with get_db_connection() as conn:
        row = conn.execute('SELECT * FROM predictions ORDER BY id DESC LIMIT 1').fetchone()
        return dict(row) if row else None
""",
    "services/traffic_service.py": """import cv2
import threading
import time
from camera.detector import VehicleDetector
from camera.tracker import VehicleTracker
from camera.vehicle_counter import VehicleCounter
from camera.speed_estimator import SpeedEstimator
import os

class VideoProcessor:
    def __init__(self):
        self.detector = VehicleDetector()
        self.tracker = VehicleTracker()
        self.counter = VehicleCounter()
        self.speed_estimator = SpeedEstimator()
        self.is_running = False
        self.thread = None
        self.latest_data = {}
        
    def start(self, video_path):
        if self.is_running: return
        if not os.path.exists(video_path):
            print(f"Video {video_path} not found.")
            return
        self.is_running = True
        self.thread = threading.Thread(target=self._process, args=(video_path,))
        self.thread.daemon = True
        self.thread.start()
        
    def stop(self):
        self.is_running = False
        
    def _process(self, video_path):
        cap = cv2.VideoCapture(video_path)
        while self.is_running and cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
                
            detections = self.detector.detect(frame)
            tracked = self.tracker.update(detections)
            counts = self.counter.update_counts(tracked)
            speeds = self.speed_estimator.estimate_speeds(tracked)
            
            total_area = frame.shape[0] * frame.shape[1]
            vehicle_area = sum([(d["x2"]-d["x1"])*(d["y2"]-d["y1"]) for d in detections])
            occupancy = min(100.0, (vehicle_area / total_area) * 100 * 5)
            
            self.latest_data = {
                "car_count": counts["car_count"],
                "bike_count": counts["bike_count"],
                "bus_count": counts["bus_count"],
                "truck_count": counts["truck_count"],
                "vehicle_count": counts["total_count"],
                "average_speed": speeds["average_speed"],
                "occupancy": round(occupancy, 2),
                "traffic_density": round(occupancy * 1.1, 2)
            }
            
            time.sleep(0.03) 
        cap.release()

video_processor = VideoProcessor()
""",
    "app.py": """from flask import Flask, render_template, jsonify, request
from services.traffic_service import video_processor
from sensors.simulator import SensorSimulator
from ml.predict import Predictor
from services.data_service import init_db, insert_traffic_record, insert_prediction, get_latest_traffic, get_latest_prediction, get_traffic_history
import threading
import time
import os

app = Flask(__name__)
sensor_sim = SensorSimulator()
predictor = Predictor()

init_db()

demo_active = False

def data_fusion_loop():
    global demo_active
    while True:
        if demo_active:
            camera_data = video_processor.latest_data
            sensor_data = sensor_sim.get_latest_reading()
            
            if camera_data:
                fused_data = {
                    "vehicle_count": (camera_data.get("vehicle_count", 0) + sensor_data["vehicle_count"]) // 2,
                    "car_count": camera_data.get("car_count", 0),
                    "bike_count": camera_data.get("bike_count", 0),
                    "bus_count": camera_data.get("bus_count", 0),
                    "truck_count": camera_data.get("truck_count", 0),
                    "average_speed": round((camera_data.get("average_speed", 0) + sensor_data["average_speed"]) / 2, 2),
                    "occupancy": round((camera_data.get("occupancy", 0) + sensor_data["occupancy"]) / 2, 2),
                    "traffic_density": round((camera_data.get("traffic_density", 0) + sensor_data["traffic_density"]) / 2, 2),
                }
            else:
                fused_data = sensor_data
                
            insert_traffic_record(fused_data)
            
            prediction = predictor.predict(fused_data)
            if prediction:
                insert_prediction(prediction)
                
        time.sleep(5)

fusion_thread = threading.Thread(target=data_fusion_loop, daemon=True)
fusion_thread.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/health')
def health():
    return jsonify({"status": "ok"})

@app.route('/api/demo/start', methods=['POST'])
def start_demo():
    global demo_active
    video_processor.start('data/videos/traffic.mp4')
    demo_active = True
    return jsonify({"status": "demo started"})

@app.route('/api/demo/stop', methods=['POST'])
def stop_demo():
    global demo_active
    video_processor.stop()
    demo_active = False
    return jsonify({"status": "demo stopped"})

@app.route('/api/traffic/current')
def current_traffic():
    data = get_latest_traffic()
    if not data:
        return jsonify({"error": "No data available"}), 404
    return jsonify(data)

@app.route('/api/predictions/latest')
def latest_prediction():
    data = get_latest_prediction()
    if not data:
        return jsonify({"error": "No prediction available"}), 404
    return jsonify(data)

@app.route('/api/traffic/history')
def traffic_history():
    data = get_traffic_history()
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
""",
    "templates/index.html": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Traffic Flow Prediction Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <nav class="navbar navbar-dark bg-dark">
        <div class="container-fluid">
            <a class="navbar-brand" href="#">🚦 Traffic Flow Prediction</a>
            <div class="d-flex">
                <button id="btn-start" class="btn btn-success me-2">Start Demo</button>
                <button id="btn-stop" class="btn btn-danger">Stop Demo</button>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="row">
            <!-- Current Status -->
            <div class="col-md-8">
                <div class="card mb-4">
                    <div class="card-header bg-primary text-white">Current Traffic Status</div>
                    <div class="card-body">
                        <div class="row text-center">
                            <div class="col-md-3">
                                <h5 class="card-title">Vehicles</h5>
                                <p class="card-text display-6" id="curr-vehicles">-</p>
                            </div>
                            <div class="col-md-3">
                                <h5 class="card-title">Density</h5>
                                <p class="card-text display-6" id="curr-density">-</p>
                            </div>
                            <div class="col-md-3">
                                <h5 class="card-title">Avg Speed</h5>
                                <p class="card-text display-6" id="curr-speed">-</p>
                            </div>
                            <div class="col-md-3">
                                <h5 class="card-title">Status</h5>
                                <p class="card-text display-6" id="curr-status">UNKNOWN</p>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Charts -->
                <div class="card mb-4">
                    <div class="card-header">Traffic Flow Trend</div>
                    <div class="card-body">
                        <canvas id="trafficChart" height="100"></canvas>
                    </div>
                </div>
            </div>

            <!-- Predictions and Breakdown -->
            <div class="col-md-4">
                <div class="card mb-4">
                    <div class="card-header bg-warning text-dark">Prediction (Next 10 Mins)</div>
                    <div class="card-body">
                        <h5 class="card-title">Predicted Vehicles: <span id="pred-vehicles">-</span></h5>
                        <h5 class="card-title">Predicted Density: <span id="pred-density">-</span></h5>
                        <h5 class="card-title">Predicted Status: <span id="pred-status">-</span></h5>
                    </div>
                </div>

                <div class="card mb-4">
                    <div class="card-header bg-info text-white">Vehicle Breakdown</div>
                    <div class="card-body">
                        <ul class="list-group">
                            <li class="list-group-item d-flex justify-content-between align-items-center">
                                Cars
                                <span class="badge bg-primary rounded-pill" id="count-cars">-</span>
                            </li>
                            <li class="list-group-item d-flex justify-content-between align-items-center">
                                Bikes
                                <span class="badge bg-primary rounded-pill" id="count-bikes">-</span>
                            </li>
                            <li class="list-group-item d-flex justify-content-between align-items-center">
                                Buses
                                <span class="badge bg-primary rounded-pill" id="count-buses">-</span>
                            </li>
                            <li class="list-group-item d-flex justify-content-between align-items-center">
                                Trucks
                                <span class="badge bg-primary rounded-pill" id="count-trucks">-</span>
                            </li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="/static/js/api.js"></script>
    <script src="/static/js/charts.js"></script>
    <script src="/static/js/dashboard.js"></script>
</body>
</html>
""",
    "static/css/style.css": """
body {
    background-color: #f8f9fa;
}
.card {
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}
.display-6 {
    font-size: 2rem;
    font-weight: 300;
}
""",
    "static/js/api.js": """
const API = {
    startDemo: () => fetch('/api/demo/start', { method: 'POST' }),
    stopDemo: () => fetch('/api/demo/stop', { method: 'POST' }),
    getCurrentTraffic: () => fetch('/api/traffic/current').then(res => res.json()),
    getLatestPrediction: () => fetch('/api/predictions/latest').then(res => res.json()),
    getTrafficHistory: () => fetch('/api/traffic/history').then(res => res.json())
};
""",
    "static/js/charts.js": """
let trafficChart;

function initChart() {
    const ctx = document.getElementById('trafficChart').getContext('2d');
    trafficChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Vehicle Count',
                data: [],
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

function updateChart(historyData) {
    if (!trafficChart) return;
    
    const labels = historyData.map(d => {
        const date = new Date(d.timestamp);
        return date.toLocaleTimeString();
    });
    const data = historyData.map(d => d.vehicle_count);
    
    trafficChart.data.labels = labels;
    trafficChart.data.datasets[0].data = data;
    trafficChart.update();
}
""",
    "static/js/dashboard.js": """
document.addEventListener('DOMContentLoaded', () => {
    initChart();

    document.getElementById('btn-start').addEventListener('click', () => {
        API.startDemo().then(() => alert('Demo started!'));
    });

    document.getElementById('btn-stop').addEventListener('click', () => {
        API.stopDemo().then(() => alert('Demo stopped!'));
    });

    function updateDashboard() {
        API.getCurrentTraffic().then(data => {
            if (data.error) return;
            document.getElementById('curr-vehicles').innerText = data.vehicle_count;
            document.getElementById('curr-density').innerText = data.traffic_density + '%';
            document.getElementById('curr-speed').innerText = data.average_speed + ' km/h';
            
            let status = "LOW";
            if(data.traffic_density > 35) status = "MEDIUM";
            if(data.traffic_density > 70) status = "HIGH";
            document.getElementById('curr-status').innerText = status;

            document.getElementById('count-cars').innerText = data.car_count;
            document.getElementById('count-bikes').innerText = data.bike_count;
            document.getElementById('count-buses').innerText = data.bus_count;
            document.getElementById('count-trucks').innerText = data.truck_count;
        }).catch(err => console.error(err));

        API.getLatestPrediction().then(data => {
            if (data.error) return;
            document.getElementById('pred-vehicles').innerText = data.predicted_vehicle_count;
            document.getElementById('pred-density').innerText = data.predicted_density + '%';
            document.getElementById('pred-status').innerText = data.congestion_level;
        }).catch(err => console.error(err));

        API.getTrafficHistory().then(data => {
            if (!data.error) {
                updateChart(data);
            }
        }).catch(err => console.error(err));
    }

    // Update every 5 seconds
    setInterval(updateDashboard, 5000);
});
""",
    "tests/__init__.py": "",
    "tests/test_api.py": """import unittest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app

class APITestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def test_health(self):
        response = self.app.get('/api/health')
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
"""
}

for rel_path, content in files.items():
    full_path = os.path.join(base_dir, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

print("Files created successfully.")
