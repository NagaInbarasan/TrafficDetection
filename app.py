from flask import Flask, render_template, jsonify, request
from services.video_processing_service import video_processor
from sensors.simulator import SensorSimulator
from services.data_service import init_db, get_latest_traffic, get_latest_prediction, get_traffic_history
from api.video_routes import video_bp
import os

app = Flask(__name__)
app.register_blueprint(video_bp)

# Simulated sensor is strictly isolated and clearly labelled
sensor_sim = SensorSimulator()

# Initialize DB tables
init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/health')
def health():
    return jsonify({
        "status": "ok",
        "processor_status": video_processor.state["status"],
        "device": video_processor.state["device"],
        "model": video_processor.state["model_name"]
    })

@app.route('/api/traffic/current')
def current_traffic():
    """
    Returns current live camera detection & traffic metrics directly from video processor.
    Never simulated or hardcoded.
    """
    st = video_processor.state
    return jsonify({
        "session_id": st["session_id"],
        "status": st["status"],
        "filename": st["filename"],
        "video_time_sec": st["video_time_sec"],
        "vehicles_on_screen": st["vehicles_on_screen"],
        "active_tracked": st["active_tracked"],
        "direction_a_count": st["dir_a"]["total"],
        "direction_b_count": st["dir_b"]["total"],
        "total_crossings": st["total_crossings"],
        "dir_a_breakdown": st["dir_a"],
        "dir_b_breakdown": st["dir_b"],
        "average_speed": st["estimated_speed"],
        "occupancy_proxy": st["occupancy_proxy"],
        "congestion_level": st["congestion_level"],
        "fps": st["fps"],
        "inference_ms": st["inference_ms"],
        "device": st["device"],
        "model_name": st["model_name"]
    })

@app.route('/api/predictions/latest')
def latest_prediction():
    """
    Returns the empirical time-series forecast generated from the video's observed traffic history.
    """
    forecast_data = video_processor.state.get("forecast", {})
    return jsonify({
        "session_id": video_processor.session_id,
        "video_time_sec": video_processor.state["video_time_sec"],
        "forecast": forecast_data,
        "congestion_level": video_processor.state["congestion_level"],
        "occupancy_proxy": video_processor.state["occupancy_proxy"]
    })

@app.route('/api/traffic/history')
def traffic_history():
    """
    Returns empirical time-series windows from the active video session.
    """
    in_memory = video_processor.forecaster.get_history_series()
    if in_memory:
        return jsonify(in_memory)
    # Fallback to database
    db_hist = get_traffic_history()
    return jsonify(db_hist)

@app.route('/api/sensors/status')
def sensor_status():
    """
    Isolated simulated sensor readings.
    Clearly labelled as SIMULATED SENSOR so it is not confused with camera AI.
    """
    reading = sensor_sim.get_latest_reading()
    return jsonify({
        "label": "[SIMULATED SENSOR — FOR TESTING ONLY]",
        "is_simulated": True,
        "data": reading
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000, threaded=True)
