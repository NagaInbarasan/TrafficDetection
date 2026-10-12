# Traffic Flow Prediction Using Camera + Sensor Data

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
   Windows: `venv\Scripts\activate`
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
