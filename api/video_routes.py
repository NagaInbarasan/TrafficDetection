from flask import Blueprint, jsonify, request, Response, send_from_directory
from services.video_processing_service import video_processor
from services.data_service import get_session_history
import os

video_bp = Blueprint('video', __name__)

ALLOWED_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv'}

@video_bp.route('/api/upload-video', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({"error": "No video file provided in upload request."}), 400
    file = request.files['video']
    if not file or file.filename == '':
        return jsonify({"error": "No file selected."}), 400

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({
            "error": f"Unsupported format '{ext}'. Allowed formats: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        }), 400

    os.makedirs('data/videos', exist_ok=True)
    # Sanitize filename
    safe_filename = os.path.basename(file.filename)
    filepath = os.path.join('data/videos', safe_filename)
    file.save(filepath)
    return jsonify({
        "status": "success",
        "filename": safe_filename,
        "message": f"Successfully uploaded '{safe_filename}'."
    })

@video_bp.route('/api/videos', methods=['GET'])
def list_videos():
    video_dir = 'data/videos'
    os.makedirs(video_dir, exist_ok=True)
    files = [
        f for f in os.listdir(video_dir)
        if os.path.splitext(f)[1].lower() in ALLOWED_EXTENSIONS
    ]
    return jsonify({"videos": sorted(files)})

@video_bp.route('/api/camera/start', methods=['POST'])
def start_camera():
    data = request.json or {}
    filename = data.get('video') or data.get('filename') or 'highway.mp4'
    model_name = data.get('model', 'yolo26s.pt')
    conf = data.get('conf', 0.25)
    imgsz = data.get('imgsz', 960)

    filepath = os.path.join('data/videos', filename)

    if not os.path.exists(filepath):
        return jsonify({
            "error": f"Video '{filename}' not found in data/videos. Please upload a real video file."
        }), 404

    success = video_processor.start(
        filepath,
        model_name=model_name,
        conf=conf,
        imgsz=imgsz
    )
    if success:
        return jsonify({
            "status": "started",
            "session_id": video_processor.session_id,
            "filename": filename,
            "model": model_name,
            "device": video_processor.state["device"],
            "imgsz": imgsz
        })
    else:
        err = video_processor.state.get("error_message", "Failed to start video processing.")
        return jsonify({"error": err}), 400

@video_bp.route('/api/camera/stop', methods=['POST'])
def stop_camera():
    video_processor.stop()
    return jsonify({"status": "stopped"})

@video_bp.route('/api/camera/pause', methods=['POST'])
def pause_camera():
    paused = video_processor.pause()
    return jsonify({"status": "paused" if video_processor.paused else "processing"})

@video_bp.route('/api/camera/configure-line', methods=['POST'])
def configure_line():
    data = request.json or {}
    preset = data.get('preset')
    norm_pt1 = data.get('norm_pt1')
    norm_pt2 = data.get('norm_pt2')
    reverse = data.get('reverse')

    cfg = video_processor.configure_line(
        preset=preset,
        norm_pt1=norm_pt1,
        norm_pt2=norm_pt2,
        reverse=reverse
    )
    return jsonify({"status": "updated", "line_config": cfg})

@video_bp.route('/api/camera/status')
def camera_status():
    return jsonify(video_processor.state)

@video_bp.route('/api/traffic/session-history')
def session_history():
    """
    Returns time series windows for the currently active session.
    """
    session_id = video_processor.session_id
    # Live in-memory series from forecaster
    in_memory = video_processor.forecaster.get_history_series()
    if in_memory:
        return jsonify(in_memory)
    # Fallback to database
    if session_id:
        db_history = get_session_history(session_id)
        if db_history:
            return jsonify(db_history)
    return jsonify([])

def generate_frames():
    while True:
        frame_bytes = video_processor.get_latest_frame_jpeg()
        if frame_bytes is None:
            time_wait = 0.08
            import time
            time.sleep(time_wait)
            continue

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@video_bp.route('/video_feed')
def video_feed():
    return Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@video_bp.route('/api/benchmark', methods=['GET'])
def get_benchmark_report():
    """
    Returns benchmark comparison between models (yolo26s.pt vs yolo26m.pt)
    and resolutions (960px vs 640px).
    """
    from tests.evaluate_accuracy import evaluate_video_clip
    video_path = os.path.join('data', 'videos', 'highway.mp4')
    if not os.path.exists(video_path):
        return jsonify({"error": "Default video not found for benchmark"}), 404

    s_960 = evaluate_video_clip(video_path, model_name='yolo26s.pt', imgsz=960, max_frames=50)
    s_640 = evaluate_video_clip(video_path, model_name='yolo26s.pt', imgsz=640, max_frames=50)
    m_960 = evaluate_video_clip(video_path, model_name='yolo26m.pt', imgsz=960, max_frames=50)

    return jsonify({
        "status": "completed",
        "benchmarks": {
            "yolo26s_960": s_960,
            "yolo26s_640": s_640,
            "yolo26m_960": m_960
        },
        "disclaimer": "Empirical benchmark measured on current GPU/CPU setup. Ground truth bounding box annotations not supplied for mAP calculation."
    })

