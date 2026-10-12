# Traffic Flow Prediction Using Camera + Sensor Data

## 1. Project Overview

**Traffic Flow Prediction Using Camera + Sensor Data** is a prototype intelligent traffic-monitoring system that combines:

- Camera/video input for vehicle detection and counting
- Sensor data for traffic measurements
- Data preprocessing and feature extraction
- Machine Learning for traffic-flow prediction
- A web dashboard for visualization and monitoring

The prototype is designed as a complete software system that can run with a **pre-recorded traffic video** and **simulated sensor data**, making it suitable for a college project/demo without requiring physical IoT hardware.

---

# 2. Main Objective

The system should:

1. Capture traffic information from a camera/video.
2. Detect and count vehicles.
3. Receive or simulate sensor measurements.
4. Combine camera and sensor features.
5. Preprocess the collected data.
6. Send the features to an ML model.
7. Predict future traffic flow and congestion.
8. Display current and predicted traffic conditions on a dashboard.

---

# 3. High-Level Workflow

```text
                 ┌──────────────────────┐
                 │   Traffic Camera     │
                 │  Live / Video File   │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │ Vehicle Detection    │
                 │     & Tracking       │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │ Vehicle Count /      │
                 │ Speed Estimation     │
                 └──────────┬───────────┘
                            │
                            │
                            ▼
┌──────────────────────┐  ┌──────────────────────┐
│  Traffic Sensors     │  │   Data Integration   │
│ count / speed /      ├─►│ Camera + Sensor Data  │
│ occupancy / etc.     │  └──────────┬───────────┘
└──────────────────────┘             │
                                     ▼
                          ┌──────────────────────┐
                          │ Data Preprocessing   │
                          │ Cleaning / Scaling   │
                          └──────────┬───────────┘
                                     │
                                     ▼
                          ┌──────────────────────┐
                          │ Feature Extraction   │
                          └──────────┬───────────┘
                                     │
                                     ▼
                          ┌──────────────────────┐
                          │   ML Prediction      │
                          │ Random Forest /      │
                          │ Regression Model     │
                          └──────────┬───────────┘
                                     │
                                     ▼
                          ┌──────────────────────┐
                          │ Traffic Prediction   │
                          │ Flow + Congestion    │
                          └──────────┬───────────┘
                                     │
                                     ▼
                          ┌──────────────────────┐
                          │ Web Dashboard        │
                          │ Charts / Status /    │
                          │ Prediction           │
                          └──────────────────────┘
```

---

# 4. Complete Project Workflow

## Step 1 — Camera Input

The system receives a traffic video from:

- Pre-recorded `.mp4` file
- Webcam
- IP camera (future extension)

Example:

```text
data/videos/traffic.mp4
```

The video is processed frame by frame using OpenCV.

---

## Step 2 — Vehicle Detection

Each frame is analyzed to identify vehicles.

Possible vehicle classes:

- Car
- Bike
- Bus
- Truck
- Auto

For the prototype, vehicle detection can be implemented using OpenCV-based methods or a pretrained object-detection model.

Output example:

```text
Frame: 1024
Cars: 18
Bikes: 11
Buses: 2
Trucks: 1
Total: 32
```

---

## Step 3 — Vehicle Tracking and Counting

Detected vehicles can be tracked across frames.

The system calculates:

```text
Vehicle Count
Vehicle Type Count
Approximate Speed
Traffic Occupancy
```

A virtual counting line can be used to avoid counting the same vehicle repeatedly.

Example:

```text
                   ROAD
─────────────────────────────────
        🚗       🏍️     🚗
─────────────────────────────────
-------------- COUNT LINE -------
             ↑
       Vehicle crossing
```

---

# 5. Sensor Data

The prototype supports sensor data such as:

- Vehicle count
- Average speed
- Road occupancy
- Traffic density
- Distance/ultrasonic measurement
- Environmental values (optional)

For a software-only prototype, sensors can be simulated.

Example sensor record:

```json
{
  "timestamp": "2026-10-07 10:15:00",
  "vehicle_count": 42,
  "average_speed": 31.5,
  "occupancy": 67.2
}
```

Future hardware can use:

- ESP32
- Arduino
- Raspberry Pi
- IR sensors
- Ultrasonic sensors

---

# 6. Data Integration

Camera and sensor data are combined using a common timestamp or time window.

Example:

```text
Camera Data
    vehicle_count = 40
    bike_count = 15
    car_count = 20
    bus_count = 3
    truck_count = 2

Sensor Data
    vehicle_count = 42
    avg_speed = 31.5 km/h
    occupancy = 67.2 %

                │
                ▼

Combined Feature Record
    vehicle_count = 41
    avg_speed = 31.5
    occupancy = 67.2
    cars = 20
    bikes = 15
    buses = 3
    trucks = 2
```

The integration layer creates a unified traffic record.

---

# 7. Data Preprocessing

Raw data should be cleaned before ML prediction.

### Operations

```text
Raw Data
   │
   ├── Handle missing values
   ├── Remove invalid readings
   ├── Remove duplicate records
   ├── Convert timestamps
   ├── Normalize / scale values
   └── Create time-based features
          │
          ▼
     Clean Dataset
```

Useful time features:

```text
hour
minute
day_of_week
is_weekend
peak_hour
```

---

# 8. Feature Extraction

The ML model uses features such as:

| Feature | Description |
|---|---|
| vehicle_count | Number of detected vehicles |
| car_count | Number of cars |
| bike_count | Number of bikes |
| bus_count | Number of buses |
| truck_count | Number of trucks |
| average_speed | Average traffic speed |
| occupancy | Percentage of road occupancy |
| traffic_density | Estimated vehicle density |
| hour | Hour of the day |
| day_of_week | Day of the week |
| peak_hour | Peak traffic indicator |

Example ML input:

```text
[
  41,
  20,
  15,
  3,
  2,
  31.5,
  67.2,
  72.0,
  10,
  2,
  1
]
```

---

# 9. Machine Learning Layer

The ML layer predicts future traffic flow.

Possible prototype models:

### Regression

Used when the target is a numeric value such as:

```text
Predicted vehicle count = 145
```

Suitable models:

- Linear Regression
- Random Forest Regressor
- Gradient Boosting Regressor

### Classification

Used to predict congestion level:

```text
LOW
MEDIUM
HIGH
```

Suitable models:

- Logistic Regression
- Random Forest Classifier
- Decision Tree
- Gradient Boosting

### Recommended prototype approach

Use two outputs:

```text
Model 1 → Predict vehicle count
Model 2 → Predict congestion level
```

---

# 10. Prediction Flow

```text
Current Traffic Data
        │
        ▼
Feature Extraction
        │
        ▼
ML Model
        │
        ├──────────────► Predicted Vehicle Count
        │
        └──────────────► Predicted Congestion
                              │
                              ▼
                      Dashboard Visualization
```

Example result:

```text
Current Vehicles : 124
Predicted Vehicles (10 min) : 147

Current Density : 68 %
Predicted Density : 76 %

Current Status : MEDIUM
Predicted Status : HIGH
```

---

# 11. Congestion Classification

A simple prototype rule can classify traffic based on traffic density or predicted vehicle count.

Example:

```text
0–35%   → LOW
36–70%  → MEDIUM
71–100% → HIGH
```

This threshold can later be replaced with a learned classification model.

---

# 12. Backend Workflow

The Flask backend acts as the main controller.

```text
Frontend Request
       │
       ▼
Flask API
       │
       ├── Camera Processing
       ├── Sensor Data
       ├── Data Preprocessing
       ├── ML Prediction
       └── Database
       │
       ▼
JSON Response
       │
       ▼
Frontend Dashboard
```

Example API endpoints:

```text
GET  /api/traffic/current
GET  /api/traffic/history
POST /api/sensor
POST /api/predict
POST /api/upload-video
GET  /api/health
```

---

# 13. Database Workflow

SQLite can be used for the prototype.

Suggested tables:

## traffic_records

```text
id
timestamp
vehicle_count
car_count
bike_count
bus_count
truck_count
average_speed
occupancy
traffic_density
```

## predictions

```text
id
timestamp
predicted_vehicle_count
predicted_density
congestion_level
prediction_horizon
```

## sensor_records

```text
id
timestamp
sensor_name
vehicle_count
average_speed
occupancy
```

---

# 14. Web Dashboard

The frontend displays the system state in a simple traffic-monitoring dashboard.

### Dashboard components

```text
┌────────────────────────────────────────────────┐
│          TRAFFIC FLOW PREDICTION               │
├────────────────────────────────────────────────┤
│                                                │
│  Vehicles       Density       Avg Speed        │
│    124            68%          31.5 km/h       │
│                                                │
├────────────────────────────────────────────────┤
│                                                │
│             Traffic Flow Chart                 │
│          Actual ───── Predicted                │
│                                                │
├────────────────────────────────────────────────┤
│                                                │
│  Current Traffic       MEDIUM                  │
│  Predicted Traffic     HIGH                    │
│  Prediction Horizon    10 minutes              │
│                                                │
├────────────────────────────────────────────────┤
│ [Start Camera] [Upload Video] [Predict]        │
└────────────────────────────────────────────────┘
```

---

# 15. Project Structure

```text
traffic-flow-prediction/
│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── camera/
│   ├── __init__.py
│   ├── detector.py
│   ├── tracker.py
│   ├── vehicle_counter.py
│   └── speed_estimator.py
│
├── sensors/
│   ├── __init__.py
│   ├── simulator.py
│   └── sensor_processor.py
│
├── ml/
│   ├── __init__.py
│   ├── train.py
│   ├── predict.py
│   ├── preprocess.py
│   ├── evaluate.py
│   ├── model.pkl
│   └── metadata.json
│
├── data/
│   ├── raw/
│   │   ├── traffic.csv
│   │   └── sensors.csv
│   │
│   ├── processed/
│   │   └── traffic_features.csv
│   │
│   └── videos/
│       └── traffic.mp4
│
├── database/
│   ├── traffic.db
│   └── schema.sql
│
├── services/
│   ├── traffic_service.py
│   ├── prediction_service.py
│   └── data_service.py
│
├── api/
│   ├── __init__.py
│   ├── traffic_routes.py
│   ├── sensor_routes.py
│   └── prediction_routes.py
│
├── templates/
│   └── index.html
│
├── static/
│   ├── css/
│   │   └── style.css
│   │
│   ├── js/
│   │   ├── dashboard.js
│   │   ├── charts.js
│   │   └── api.js
│   │
│   └── assets/
│       └── icons/
│
└── tests/
    ├── test_camera.py
    ├── test_sensors.py
    ├── test_ml.py
    └── test_api.py
```

---

# 16. File-by-File Responsibilities

## Root

### `app.py`

Main Flask application.

Responsibilities:

- Start the server
- Register API routes
- Initialize services
- Serve the dashboard

---

### `requirements.txt`

Python dependencies.

Example:

```text
flask
opencv-python
numpy
pandas
scikit-learn
joblib
```

---

# 17. Camera Module

## `camera/detector.py`

Responsible for detecting vehicles in each frame.

```text
Input  → Video Frame
Output → Detected Vehicles
```

Example:

```python
[
    {"type": "car", "x": 120, "y": 200},
    {"type": "bike", "x": 340, "y": 250}
]
```

---

## `camera/tracker.py`

Tracks detected vehicles between frames.

Purpose:

- Assign vehicle IDs
- Prevent duplicate counting
- Track movement

---

## `camera/vehicle_counter.py`

Counts vehicles crossing a virtual line or region.

Output:

```text
cars = 20
bikes = 15
buses = 3
trucks = 2
total = 40
```

---

## `camera/speed_estimator.py`

Estimates vehicle speed from movement between frames.

Prototype calculation:

```text
Speed ≈ Distance / Time
```

Camera calibration can be added later for better real-world accuracy.

---

# 18. Sensor Module

## `sensors/simulator.py`

Generates realistic sample traffic readings.

Example:

```text
Time       Vehicles    Speed    Occupancy
10:00         35       42.0       40%
10:05         47       36.5       52%
10:10         63       29.2       68%
10:15         78       24.7       81%
```

This allows the complete system to work without physical sensors.

---

## `sensors/sensor_processor.py`

Responsibilities:

- Validate sensor readings
- Clean values
- Convert units
- Aggregate readings
- Synchronize timestamps

---

# 19. Machine Learning Module

## `ml/preprocess.py`

Prepares raw data for training and prediction.

```text
Raw CSV
  ↓
Cleaning
  ↓
Feature Engineering
  ↓
Train/Test Split
  ↓
Processed Features
```

---

## `ml/train.py`

Trains the prediction model.

Example:

```text
Input:
historical traffic features

Output:
model.pkl
```

---

## `ml/predict.py`

Loads the saved model and generates predictions.

```text
Current Features
       ↓
   model.pkl
       ↓
Prediction
```

---

## `ml/evaluate.py`

Evaluates model performance.

Possible metrics:

### Regression

```text
MAE
RMSE
R² Score
```

### Classification

```text
Accuracy
Precision
Recall
F1 Score
```

---

# 20. Services Layer

The service layer connects the API with the processing and ML modules.

## `services/traffic_service.py`

Handles:

- Current traffic state
- Traffic history
- Camera results
- Traffic calculations

## `services/prediction_service.py`

Handles:

- Feature preparation
- Model loading
- Prediction
- Congestion classification

## `services/data_service.py`

Handles:

- Database insertion
- Database retrieval
- Historical records

---

# 21. API Layer

## `api/traffic_routes.py`

Traffic-related endpoints.

Example:

```text
GET /api/traffic/current
GET /api/traffic/history
```

---

## `api/sensor_routes.py`

Sensor-related endpoints.

Example:

```text
POST /api/sensor
```

Request:

```json
{
  "vehicle_count": 40,
  "average_speed": 32,
  "occupancy": 65
}
```

---

## `api/prediction_routes.py`

Prediction-related endpoints.

Example:

```text
POST /api/predict
```

Response:

```json
{
  "predicted_vehicle_count": 145,
  "predicted_density": 76,
  "congestion": "HIGH"
}
```

---

# 22. Frontend File Responsibilities

## `templates/index.html`

Main dashboard structure.

Contains:

- Metric cards
- Camera area
- Charts
- Prediction section
- Controls

---

## `static/css/style.css`

Controls:

- Layout
- Cards
- Buttons
- Tables
- Responsive design
- Traffic status indicators

---

## `static/js/api.js`

Centralized API calls.

Example:

```javascript
fetch("/api/traffic/current")
```

---

## `static/js/dashboard.js`

Updates dashboard values.

Example:

```text
Vehicle count
Density
Average speed
Current congestion
Predicted congestion
```

---

## `static/js/charts.js`

Creates charts using Chart.js.

Recommended charts:

```text
1. Vehicles vs Time
2. Speed vs Time
3. Density vs Time
4. Actual vs Predicted Traffic
```

---

# 23. End-to-End Data Flow

```text
                 ┌─────────────┐
                 │ Video Frame │
                 └──────┬──────┘
                        ▼
                 Vehicle Detector
                        │
                        ▼
                  Vehicle Tracker
                        │
                        ▼
                 Vehicle Counter
                        │
             ┌──────────┴──────────┐
             │                     │
             ▼                     ▼
       Vehicle Counts        Speed Estimate
             │                     │
             └──────────┬──────────┘
                        │
                        ▼
                Camera Features
                        │
                        │
Sensor Data ────────────┤
                        ▼
                 Data Integration
                        │
                        ▼
                  Preprocessing
                        │
                        ▼
                Feature Extraction
                        │
                        ▼
                     ML Model
                        │
             ┌──────────┴──────────┐
             ▼                     ▼
      Flow Prediction       Congestion Prediction
             │                     │
             └──────────┬──────────┘
                        ▼
                  SQLite Database
                        │
                        ▼
                    Flask API
                        │
                        ▼
                 Web Dashboard
                        │
           ┌────────────┼────────────┐
           ▼            ▼            ▼
        Numbers       Charts      Status
```

---

# 24. Data Lifecycle

```text
COLLECT
  ↓
Camera + Sensors
  ↓
DETECT
  ↓
Vehicles
  ↓
MEASURE
  ↓
Count + Speed + Occupancy
  ↓
COMBINE
  ↓
Unified Traffic Record
  ↓
CLEAN
  ↓
Preprocessed Dataset
  ↓
PREDICT
  ↓
ML Model
  ↓
STORE
  ↓
Database
  ↓
DISPLAY
  ↓
Dashboard
```

---

# 25. Example Data Record

A unified record may look like:

```json
{
  "timestamp": "2026-10-07T10:15:00",
  "vehicle_count": 41,
  "car_count": 20,
  "bike_count": 15,
  "bus_count": 3,
  "truck_count": 2,
  "average_speed": 31.5,
  "occupancy": 67.2,
  "traffic_density": 72.0
}
```

Prediction:

```json
{
  "timestamp": "2026-10-07T10:15:00",
  "prediction_horizon_minutes": 10,
  "predicted_vehicle_count": 147,
  "predicted_density": 76.0,
  "congestion_level": "HIGH"
}
```

---

# 26. Recommended Prototype Execution

## Mode A — Demo Mode

Use:

```text
Video File
   +
Sensor Simulator
   +
Trained ML Model
```

This is the easiest complete demonstration.

---

## Mode B — Webcam Mode

```text
Webcam
   ↓
Vehicle Detection
   ↓
Traffic Features
   ↓
ML Prediction
   ↓
Dashboard
```

---

## Mode C — Future IoT Mode

```text
Camera
   +
ESP32 Sensors
   ↓
Network / MQTT
   ↓
Flask Backend
   ↓
ML Model
   ↓
Dashboard
```

---

# 27. Recommended Technology Stack

| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript |
| Dashboard Charts | Chart.js |
| Backend | Python + Flask |
| Computer Vision | OpenCV |
| Data Processing | Pandas + NumPy |
| Machine Learning | Scikit-learn |
| Model Serialization | Joblib |
| Database | SQLite |
| Sensor Prototype | Python Simulator |
| Version Control | Git + GitHub |

---

# 28. Development Order

Build the prototype in this order:

```text
1. Create project structure
        ↓
2. Prepare traffic dataset
        ↓
3. Build sensor simulator
        ↓
4. Build camera vehicle detection
        ↓
5. Implement vehicle counting
        ↓
6. Combine camera + sensor data
        ↓
7. Build preprocessing pipeline
        ↓
8. Train ML model
        ↓
9. Create Flask API
        ↓
10. Create dashboard
        ↓
11. Connect dashboard to API
        ↓
12. Store historical data
        ↓
13. Test complete workflow
```

---

# 29. Minimum Viable Prototype (MVP)

For the first working version, implement only:

```text
Camera Video
    ↓
Vehicle Count
    +
Simulated Sensor Data
    ↓
Feature Combination
    ↓
Random Forest Model
    ↓
Traffic Prediction
    ↓
Flask API
    ↓
Web Dashboard
```

### MVP output

```text
Current Vehicles: 124

Current Density: 68%

Average Speed: 31 km/h

Predicted Vehicles (10 min): 147

Predicted Congestion: HIGH
```

---

# 30. Future Extensions

Possible upgrades:

- Real-time CCTV/IP camera integration
- YOLO-based vehicle detection
- Multi-camera traffic monitoring
- MQTT sensor communication
- ESP32 hardware integration
- LSTM/GRU time-series prediction
- Traffic signal optimization
- Accident detection
- Emergency vehicle detection
- Route congestion prediction
- Map-based traffic visualization
- Cloud deployment
- Mobile application
- Edge AI deployment on Raspberry Pi

---

# 31. Final System Architecture

```text
┌──────────────────────────────────────────────────────────┐
│                    TRAFFIC SYSTEM                        │
│                                                          │
│  ┌──────────────┐          ┌────────────────┐            │
│  │ Traffic      │          │ IoT / Sensor   │            │
│  │ Camera       │          │ Data           │            │
│  └──────┬───────┘          └───────┬────────┘            │
│         │                          │                     │
│         ▼                          ▼                     │
│  ┌──────────────┐          ┌────────────────┐            │
│  │ CV Detection │          │ Sensor         │            │
│  │ + Tracking   │          │ Processing     │            │
│  └──────┬───────┘          └───────┬────────┘            │
│         │                          │                     │
│         └─────────────┬────────────┘                     │
│                       ▼                                  │
│               ┌────────────────┐                         │
│               │ Data Processing │                         │
│               └───────┬────────┘                         │
│                       ▼                                  │
│               ┌────────────────┐                         │
│               │ Feature Engine  │                         │
│               └───────┬────────┘                         │
│                       ▼                                  │
│               ┌────────────────┐                         │
│               │   ML Models     │                         │
│               └───────┬────────┘                         │
│                       ▼                                  │
│          ┌─────────────────────────┐                      │
│          │ Traffic Flow Prediction │                      │
│          │ Congestion Prediction   │                      │
│          └────────────┬────────────┘                      │
│                       ▼                                  │
│               ┌────────────────┐                         │
│               │ SQLite Database │                         │
│               └───────┬────────┘                         │
│                       ▼                                  │
│               ┌────────────────┐                         │
│               │ Flask REST API  │                         │
│               └───────┬────────┘                         │
│                       ▼                                  │
│               ┌────────────────┐                         │
│               │ Web Dashboard   │                         │
│               └────────────────┘                         │
└──────────────────────────────────────────────────────────┘
```

---

# 32. One-Line Data Flow

```text
Camera + Sensors → Detection → Counting → Data Fusion → Preprocessing → Features → ML Prediction → Database → API → Dashboard
```

---

# 33. Project Deliverable

The completed prototype should demonstrate these four major technologies working together:

```text
Computer Vision
       +
IoT / Sensor Data
       +
Machine Learning
       +
Web Application
```

The key demonstration is:

**"The system observes current traffic using camera and sensor data, predicts near-future traffic flow, classifies congestion, and displays the result in a web dashboard."**
