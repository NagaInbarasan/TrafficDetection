import sqlite3
import os

DB_PATH = 'database/traffic.db'

def get_db_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    schema_path = 'database/schema.sql'
    if os.path.exists(schema_path):
        with open(schema_path, 'r') as f:
            conn.executescript(f.read())
    conn.commit()
    conn.close()

def create_session(session_id, filename, total_frames, video_fps, model_name, device):
    conn = get_db_connection()
    conn.execute('''
        INSERT OR REPLACE INTO video_sessions 
        (session_id, filename, total_frames, video_fps, model_name, device)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (session_id, filename, total_frames, video_fps, model_name, device))
    conn.commit()
    conn.close()

def record_traffic_window(session_id, win_data):
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO traffic_windows (
            session_id, window_idx, video_time_sec,
            dir_a_crossings, dir_b_crossings, total_crossings,
            flow_rate_per_min, occupancy_proxy, avg_speed
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        session_id,
        win_data.get("window_idx", 0),
        win_data.get("end_time_sec", 0.0),
        win_data.get("dir_a", 0),
        win_data.get("dir_b", 0),
        win_data.get("total", 0),
        win_data.get("flow_rate_per_min", 0.0),
        win_data.get("avg_occupancy", 0.0),
        win_data.get("avg_speed", 0.0)
    ))
    conn.commit()
    conn.close()

def record_forecast(session_id, video_time_sec, forecast_data, congestion_level):
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO forecast_records (
            session_id, video_time_sec, forecast_1m, forecast_5m, forecast_10m,
            trend, confidence, congestion_level
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        session_id,
        video_time_sec,
        forecast_data.get("forecast_1min", 0),
        forecast_data.get("forecast_5min", 0),
        forecast_data.get("forecast_10min", 0),
        forecast_data.get("trend", "Stable"),
        forecast_data.get("confidence", "Low"),
        congestion_level
    ))
    conn.commit()
    conn.close()

def get_session_history(session_id, limit=60):
    conn = get_db_connection()
    rows = conn.execute('''
        SELECT video_time_sec, dir_a_crossings, dir_b_crossings, total_crossings, flow_rate_per_min, occupancy_proxy, avg_speed
        FROM traffic_windows 
        WHERE session_id = ? 
        ORDER BY window_idx ASC LIMIT ?
    ''', (session_id, limit)).fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_latest_traffic():
    conn = get_db_connection()
    row = conn.execute('SELECT * FROM traffic_windows ORDER BY id DESC LIMIT 1').fetchone()
    conn.close()
    return dict(row) if row else None

def get_latest_prediction():
    conn = get_db_connection()
    row = conn.execute('SELECT * FROM forecast_records ORDER BY id DESC LIMIT 1').fetchone()
    conn.close()
    return dict(row) if row else None

def get_traffic_history(limit=50):
    conn = get_db_connection()
    rows = conn.execute('''
        SELECT video_time_sec, dir_a_crossings as direction_a_count, dir_b_crossings as direction_b_count, 
               avg_speed as average_estimated_speed, occupancy_proxy as traffic_density 
        FROM traffic_windows 
        ORDER BY id DESC LIMIT ?
    ''', (limit,)).fetchall()
    conn.close()
    return [dict(row) for row in reversed(rows)]
