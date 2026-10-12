import cv2
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
