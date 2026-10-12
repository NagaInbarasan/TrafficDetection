import cv2
import threading
import time
import os
import math
import uuid
import numpy as np
import torch

from camera.tracker import YoloTracker
from camera.vehicle_counter import VehicleCounter
from camera.speed_estimator import SpeedEstimator
from services.forecasting_service import TrafficForecastingService
from services.data_service import create_session, record_traffic_window, record_forecast

class VideoProcessor:
    def __init__(self):
        self.default_model = 'yolo26s.pt'
        self.default_conf = 0.25
        self.default_imgsz = 960

        self.tracker = YoloTracker(
            model_name=self.default_model,
            conf=self.default_conf,
            imgsz=self.default_imgsz
        )
        self.counter = VehicleCounter()
        self.speed_estimator = SpeedEstimator()
        self.forecaster = TrafficForecastingService(window_sec=10.0)

        self.is_running = False
        self.paused = False
        self.thread = None

        self.latest_frame = None
        self.lock = threading.Lock()

        self.session_id = None
        self.current_video_path = None
        self.state = self._get_initial_state()

        # Display sizing
        self.display_width = 1280
        self.display_height = 720

    def _get_initial_state(self):
        device_str = "CUDA" if torch.cuda.is_available() else "CPU"
        return {
            "session_id": "",
            "status": "STOPPED", # STOPPED, PROCESSING, PAUSED, COMPLETED, VIDEO ERROR
            "error_message": "",
            "filename": "",
            "frame": 0,
            "total_frames": 0,
            "progress": 0.0,
            "video_fps": 30.0,
            "video_time_sec": 0.0,
            "video_duration_sec": 0.0,
            "fps": 0.0,
            "inference_ms": 0.0,
            "device": device_str,
            "model_name": self.default_model,
            "imgsz": self.default_imgsz,
            "conf_thresh": self.default_conf,
            "vehicles_on_screen": 0,
            "active_tracked": 0,
            "dir_a": {"car": 0, "motorcycle": 0, "bus": 0, "truck": 0, "bicycle": 0, "total": 0},
            "dir_b": {"car": 0, "motorcycle": 0, "bus": 0, "truck": 0, "bicycle": 0, "total": 0},
            "total_crossings": 0,
            "estimated_speed": 0.0,
            "occupancy_proxy": 0.0,
            "congestion_level": "LOW",
            "forecast": {
                "current_flow_rate_per_min": 0.0,
                "dir_a_flow_per_min": 0.0,
                "dir_b_flow_per_min": 0.0,
                "forecast_1min": 0,
                "forecast_5min": 0,
                "forecast_10min": 0,
                "forecast_1min_dir_a": 0,
                "forecast_1min_dir_b": 0,
                "forecast_5min_dir_a": 0,
                "forecast_5min_dir_b": 0,
                "forecast_10min_dir_a": 0,
                "forecast_10min_dir_b": 0,
                "trend": "Stable",
                "confidence": "Low",
                "status": "Preliminary",
                "is_preliminary": True,
                "explanation": "No video processed yet.",
                "observed_duration_sec": 0.0,
                "baseline_mae": "N/A",
                "baseline_rmse": "N/A"
            },
            "line_config": {
                "preset": self.counter.current_preset,
                "norm_pt1": self.counter.norm_pt1,
                "norm_pt2": self.counter.norm_pt2,
                "reverse_directions": self.counter.reverse_directions
            }
        }

    def configure_model(self, model_name=None, conf=None, imgsz=None):
        if model_name:
            self.default_model = model_name
        if conf is not None:
            self.default_conf = float(conf)
        if imgsz is not None:
            self.default_imgsz = int(imgsz)
        self.tracker.set_config(model_name=self.default_model, conf=self.default_conf, imgsz=self.default_imgsz)
        self.state["model_name"] = self.default_model
        self.state["conf_thresh"] = self.default_conf
        self.state["imgsz"] = self.default_imgsz

    def configure_line(self, preset=None, norm_pt1=None, norm_pt2=None, reverse=None):
        if preset:
            self.counter.set_preset(preset, self.display_width, self.display_height)
        elif norm_pt1 and norm_pt2:
            self.counter.set_line_normalized(norm_pt1, norm_pt2, self.display_width, self.display_height, preset="custom")
        if reverse is not None:
            self.counter.reverse_directions = bool(reverse)

        self.state["line_config"] = {
            "preset": self.counter.current_preset,
            "norm_pt1": self.counter.norm_pt1,
            "norm_pt2": self.counter.norm_pt2,
            "reverse_directions": self.counter.reverse_directions
        }
        return self.state["line_config"]

    def start(self, video_path, model_name=None, conf=None, imgsz=None):
        if self.is_running:
            self.stop()
            time.sleep(0.3)

        if model_name or conf or imgsz:
            self.configure_model(model_name, conf, imgsz)

        # Validate video existence
        if not video_path or not os.path.exists(video_path):
            self.state = self._get_initial_state()
            self.state["status"] = "VIDEO ERROR"
            self.state["filename"] = os.path.basename(video_path) if video_path else "None"
            self.state["error_message"] = (
                f"Unable to open '{self.state['filename']}'. Check that the video exists, "
                f"is a valid video format (.mp4, .avi, .mov, .mkv), and is not corrupted."
            )
            return False

        # Test opening with OpenCV
        test_cap = cv2.VideoCapture(video_path)
        if not test_cap.isOpened():
            self.state = self._get_initial_state()
            self.state["status"] = "VIDEO ERROR"
            self.state["filename"] = os.path.basename(video_path)
            self.state["error_message"] = f"OpenCV could not open video stream for '{self.state['filename']}'. Unsupported codec or corrupted file."
            test_cap.release()
            return False

        total_frames = int(test_cap.get(cv2.CAP_PROP_FRAME_COUNT))
        video_fps = test_cap.get(cv2.CAP_PROP_FPS)
        test_cap.release()

        if total_frames <= 0 or not video_fps or video_fps <= 0:
            video_fps = 30.0

        # Create clean session ID
        self.session_id = f"sess_{uuid.uuid4().hex[:8]}"
        self.current_video_path = video_path

        # Reset all tracking, counting, and forecasting states
        self.tracker.reset()
        self.counter.reset()
        self.speed_estimator.reset(fps=video_fps)
        self.forecaster.reset(session_id=self.session_id)
        self.paused = False

        self.state = self._get_initial_state()
        self.state["session_id"] = self.session_id
        self.state["filename"] = os.path.basename(video_path)
        self.state["total_frames"] = total_frames
        self.state["video_fps"] = round(video_fps, 2)
        self.state["video_duration_sec"] = round(total_frames / video_fps, 1) if total_frames > 0 else 0.0
        self.state["status"] = "PROCESSING"

        # Record session in database
        try:
            create_session(
                self.session_id,
                self.state["filename"],
                total_frames,
                self.state["video_fps"],
                self.tracker.model_name,
                self.tracker.device
            )
        except Exception as e:
            print(f"[VideoProcessor] DB create_session error: {e}")

        self.is_running = True
        self.thread = threading.Thread(target=self._process_loop, args=(video_path, video_fps))
        self.thread.daemon = True
        self.thread.start()
        return True

    def stop(self):
        self.is_running = False
        self.paused = False
        self.state["status"] = "STOPPED"

    def pause(self):
        if self.is_running:
            self.paused = not self.paused
            self.state["status"] = "PAUSED" if self.paused else "PROCESSING"
            return True
        return False

    def get_latest_frame_jpeg(self):
        with self.lock:
            if self.latest_frame is None:
                return None
            # JPEG Quality 90 for clean display quality without lag
            ret, buffer = cv2.imencode('.jpg', self.latest_frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
            return buffer.tobytes() if ret else None

    def _process_loop(self, video_path, video_fps):
        cap = cv2.VideoCapture(video_path)
        frame_idx = 0
        last_calc_time = time.time()
        fps_smoothed = 0.0

        # Vehicle class distinct colors (BGR)
        class_colors = {
            'car': (255, 120, 50),        # Blue/Cyan
            'motorcycle': (50, 220, 255), # Yellow
            'bus': (60, 60, 255),         # Red
            'truck': (200, 50, 200),      # Purple/Magenta
            'bicycle': (80, 230, 80),     # Bright Green
            'vehicle': (220, 220, 220)
        }

        # Last forecast update time
        last_forecast_time = 0.0

        while self.is_running and cap.isOpened():
            if self.paused:
                time.sleep(0.08)
                continue

            frame_start_time = time.time()
            ret, frame = cap.read()
            if not ret:
                # Video ended cleanly
                self.state["status"] = "COMPLETED"
                self.state["progress"] = 100.0
                break

            frame_idx += 1
            source_video_time_sec = round(frame_idx / video_fps, 2)

            # Resize to standard high-def display resolution preserving quality
            h, w = frame.shape[:2]
            if (w, h) != (self.display_width, self.display_height):
                frame = cv2.resize(frame, (self.display_width, self.display_height))

            # Update counting line coordinates to frame dimensions
            self.counter.update_pixel_coords(self.display_width, self.display_height)

            # 1. Run ByteTrack Persistent YOLO Detection
            detections, inference_ms, device_str = self.tracker.track(frame, frame_idx=frame_idx)

            # 2. Update Directional Counting with geometric line crossing
            counter_results = self.counter.update_counts(
                detections,
                frame_idx=frame_idx,
                video_time_sec=source_video_time_sec
            )

            # 3. Estimate Relative Speeds
            speed_info = self.speed_estimator.estimate_speeds(detections)
            avg_speed = speed_info["average_speed"]

            # 4. Compute Documented Road Occupancy Proxy (%)
            total_frame_area = self.display_width * self.display_height
            occupied_area = sum((d["x2"] - d["x1"]) * (d["y2"] - d["y1"]) for d in detections)
            # Normal road surface coverage proxy
            occupancy_proxy = round(min(100.0, (occupied_area / float(total_frame_area)) * 100.0 * 2.5), 1)

            # 5. Measure Actual Processing FPS
            frame_elapsed = time.time() - frame_start_time
            instant_fps = (1.0 / frame_elapsed) if frame_elapsed > 0 else 30.0
            fps_smoothed = round(0.85 * fps_smoothed + 0.15 * instant_fps if fps_smoothed > 0 else instant_fps, 1)

            # 6. Stream frame events to Real Time-Series Forecasting Service
            self.forecaster.process_frame_state(
                video_time_sec=source_video_time_sec,
                new_crossings=counter_results["new_crossings"],
                visible_count=len(detections),
                occupancy_proxy=occupancy_proxy,
                avg_speed=avg_speed
            )

            # Update forecast periodically (every ~1s in source video time)
            if (source_video_time_sec - last_forecast_time) >= 1.0 or last_forecast_time == 0.0:
                forecast_data = self.forecaster.generate_forecast(source_video_time_sec)
                last_forecast_time = source_video_time_sec

                # Documented Congestion Classification
                current_flow = forecast_data["current_flow_rate_per_min"]
                if occupancy_proxy > 35.0 or current_flow > 35.0:
                    congestion_level = "HIGH"
                elif occupancy_proxy > 15.0 or current_flow > 15.0:
                    congestion_level = "MEDIUM"
                else:
                    congestion_level = "LOW"

                # Update database window if a window just completed
                if self.forecaster.windows:
                    latest_win = self.forecaster.windows[-1]
                    try:
                        record_traffic_window(self.session_id, latest_win)
                        record_forecast(self.session_id, source_video_time_sec, forecast_data, congestion_level)
                    except Exception as e:
                        pass
            else:
                forecast_data = self.state["forecast"]
                congestion_level = self.state["congestion_level"]

            # 7. Annotate Frame with Real Visual AI Overlays
            self._draw_ai_overlays(
                frame,
                detections,
                counter_results,
                fps_smoothed,
                inference_ms,
                device_str,
                class_colors,
                source_video_time_sec
            )

            # 8. Update Processor State
            total_frames = self.state["total_frames"]
            progress_pct = round((frame_idx / total_frames) * 100.0 if total_frames > 0 else 0.0, 1)

            self.state.update({
                "frame": frame_idx,
                "progress": progress_pct,
                "video_time_sec": source_video_time_sec,
                "fps": fps_smoothed,
                "inference_ms": round(inference_ms, 1),
                "device": device_str,
                "vehicles_on_screen": len(detections),
                "active_tracked": len(self.tracker.track_history),
                "dir_a": counter_results["dir_a"],
                "dir_b": counter_results["dir_b"],
                "total_crossings": counter_results["total_crossings"],
                "estimated_speed": avg_speed,
                "occupancy_proxy": occupancy_proxy,
                "congestion_level": congestion_level,
                "forecast": forecast_data,
                "line_config": {
                    "preset": self.counter.current_preset,
                    "norm_pt1": self.counter.norm_pt1,
                    "norm_pt2": self.counter.norm_pt2,
                    "reverse_directions": self.counter.reverse_directions
                }
            })

            # Store latest annotated frame
            with self.lock:
                self.latest_frame = frame

            # Control playback pacing to match video FPS smoothly
            target_frame_time = 1.0 / max(10.0, video_fps)
            processing_time = time.time() - frame_start_time
            if target_frame_time > processing_time:
                time.sleep(target_frame_time - processing_time)

        cap.release()
        self.is_running = False

    def _draw_ai_overlays(self, frame, detections, counter_results, fps, inference_ms, device, colors, video_time):
        """
        Draws actual detected bounding boxes, class labels, track IDs, confidence scores,
        trajectory trails, and the configurable counting line with directional indicators.
        """
        pt1 = counter_results["line_pt1"]
        pt2 = counter_results["line_pt2"]
        rev = counter_results["reverse_directions"]

        # 1. Draw Counting Line
        line_color = (0, 220, 255) # Bright Yellow/Gold
        cv2.line(frame, pt1, pt2, line_color, 3)

        # Draw line endpoints as circles
        cv2.circle(frame, pt1, 6, (0, 255, 255), -1)
        cv2.circle(frame, pt2, 6, (0, 255, 255), -1)

        # Calculate normal vector for Direction labels
        dx = pt2[0] - pt1[0]
        dy = pt2[1] - pt1[1]
        length = math.hypot(dx, dy)
        if length > 0:
            nx = -dy / length
            ny = dx / length
        else:
            nx, ny = 0, -1

        mid_x = (pt1[0] + pt2[0]) // 2
        mid_y = (pt1[1] + pt2[1]) // 2

        # Side A label (positive side of normal)
        side_a_offset = 28
        label_a_x = int(mid_x + nx * side_a_offset)
        label_a_y = int(mid_y + ny * side_a_offset)

        # Side B label (negative side of normal)
        label_b_x = int(mid_x - nx * side_a_offset)
        label_b_y = int(mid_y - ny * side_a_offset)

        label_a_text = "DIRECTION A ↑" if not rev else "DIRECTION B ↓"
        label_b_text = "DIRECTION B ↓" if not rev else "DIRECTION A ↑"

        cv2.putText(frame, label_a_text, (max(10, label_a_x - 70), max(25, label_a_y)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 120), 2, cv2.LINE_AA)
        cv2.putText(frame, label_b_text, (max(10, label_b_x - 70), max(25, label_b_y)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (50, 150, 255), 2, cv2.LINE_AA)

        # Line Title banner
        cv2.putText(frame, "[ COUNTING LINE ]", (mid_x - 60, mid_y - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, line_color, 1, cv2.LINE_AA)

        # 2. Draw Detected Vehicles, Boxes, Trails & Direction Indicators
        for d in detections:
            cls = d["class_name"]
            c = colors.get(cls, colors['vehicle'])
            x1, y1, x2, y2 = d["x1"], d["y1"], d["x2"], d["y2"]

            # Bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), c, 2)

            # Direction Arrow based on recent trajectory movement
            history = d.get("history", [])
            arrow = ""
            if len(history) >= 3:
                move_dy = history[-1][1] - history[0][1]
                move_dx = history[-1][0] - history[0][0]
                # Dot product with normal vector
                dot = move_dx * nx + move_dy * ny
                if abs(dot) > 2.0:
                    arrow = "↑" if dot > 0 else "↓"

            # Label text
            label = f"{cls.upper()} #{d['track_id']} {int(d['confidence']*100)}% {arrow}"

            # Label background pill
            (txt_w, txt_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.52, 1)
            cv2.rectangle(frame, (x1, max(0, y1 - 20)), (x1 + txt_w + 6, y1), c, -1)
            cv2.putText(frame, label, (x1 + 3, max(14, y1 - 5)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.52, (0, 0, 0), 1, cv2.LINE_AA)

            # Trajectory trail
            if len(history) > 1:
                pts = np.array(history, np.int32).reshape((-1, 1, 2))
                cv2.polylines(frame, [pts], False, c, 2, cv2.LINE_AA)

            # Center point
            cx, cy = d["centroid"]
            cv2.circle(frame, (cx, cy), 3, c, -1)

        # 3. Compact Live HUD Overlay (Top-Left)
        hud_bg_w = 340
        hud_bg_h = 75
        cv2.rectangle(frame, (10, 10), (10 + hud_bg_w, 10 + hud_bg_h), (20, 20, 20), -1)
        cv2.rectangle(frame, (10, 10), (10 + hud_bg_w, 10 + hud_bg_h), (80, 80, 80), 1)

        hud_line1 = f"AI Device: {device} | Model: {self.tracker.model_name}"
        hud_line2 = f"FPS: {fps:.1f} | Latency: {inference_ms:.1f}ms"
        hud_line3 = f"Visible: {len(detections)} | Crossings: {counter_results['total_crossings']} | Time: {video_time:.1f}s"

        dev_color = (0, 255, 120) if device == "CUDA" else (0, 200, 255)
        cv2.putText(frame, hud_line1, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.45, dev_color, 1, cv2.LINE_AA)
        cv2.putText(frame, hud_line2, (20, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (220, 220, 220), 1, cv2.LINE_AA)
        cv2.putText(frame, hud_line3, (20, 74), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (220, 220, 220), 1, cv2.LINE_AA)

video_processor = VideoProcessor()
