-- Video Session Tracking
CREATE TABLE IF NOT EXISTS video_sessions (
    session_id TEXT PRIMARY KEY,
    filename TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    total_frames INTEGER,
    video_fps REAL,
    model_name TEXT,
    device TEXT
);

-- Real Empirical Time-Series Windows
CREATE TABLE IF NOT EXISTS traffic_windows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    window_idx INTEGER,
    video_time_sec REAL,
    dir_a_crossings INTEGER,
    dir_b_crossings INTEGER,
    total_crossings INTEGER,
    flow_rate_per_min REAL,
    occupancy_proxy REAL,
    avg_speed REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Forecast & Congestion Snapshots
CREATE TABLE IF NOT EXISTS forecast_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    video_time_sec REAL,
    forecast_1m INTEGER,
    forecast_5m INTEGER,
    forecast_10m INTEGER,
    trend TEXT,
    confidence TEXT,
    congestion_level TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Legacy Compatibility Table
CREATE TABLE IF NOT EXISTS traffic_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    video_session_id TEXT,
    visible_vehicle_count INTEGER,
    direction_a_count INTEGER,
    direction_b_count INTEGER,
    direction_a_cars INTEGER,
    direction_a_bikes INTEGER,
    direction_a_buses INTEGER,
    direction_a_trucks INTEGER,
    direction_b_cars INTEGER,
    direction_b_bikes INTEGER,
    direction_b_buses INTEGER,
    direction_b_trucks INTEGER,
    average_estimated_speed REAL,
    traffic_density REAL
);

-- Explicitly Labelled Simulated Sensor Records (Isolated from Camera AI)
CREATE TABLE IF NOT EXISTS simulated_sensor_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    sensor_name TEXT,
    simulated_vehicle_count INTEGER,
    simulated_speed REAL,
    simulated_occupancy REAL
);
