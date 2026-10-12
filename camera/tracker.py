import os
import torch
from ultralytics import YOLO

# In-memory model cache to prevent reloading weights on every frame or session
_MODEL_CACHE = {}

def get_yolo_model(model_name='yolo26s.pt', device='auto'):
    """
    Retrieves or loads a cached YOLO model.
    Falls back gracefully if weights are missing or need download.
    """
    if device == 'auto':
        target_device = 'cuda' if torch.cuda.is_available() else 'cpu'
    else:
        target_device = device

    cache_key = (model_name, target_device)
    if cache_key in _MODEL_CACHE:
        return _MODEL_CACHE[cache_key], target_device

    # Attempt to load specified model
    try:
        model = YOLO(model_name)
    except Exception as e:
        # Fallback mapping if a specific model file is missing
        fallback_map = {
            'yolo26s.pt': 'yolov8s.pt',
            'yolo26m.pt': 'yolov8m.pt',
            'yolo26n.pt': 'yolov8n.pt'
        }
        alt_name = fallback_map.get(model_name, 'yolo26s.pt')
        print(f"[YOLO] Warning: could not load {model_name} ({e}), attempting fallback to {alt_name}")
        model = YOLO(alt_name)

    model.to(target_device)
    _MODEL_CACHE[cache_key] = model
    return model, target_device


class YoloTracker:
    def __init__(self, model_name='yolo26s.pt', conf=0.25, imgsz=960, device='auto', tracker='bytetrack.yaml'):
        self.model_name = model_name
        self.conf = float(conf)
        self.imgsz = int(imgsz)
        self.tracker_cfg = tracker
        self.device_pref = device

        self.model, self.device = get_yolo_model(self.model_name, self.device_pref)

        # Dynamic class name mapping from model.names
        self.class_name_map = {}
        self.target_class_ids = []
        self._build_class_mapping()

        self.track_history = {} # track_id -> list of centroids
        self.last_seen_frame = {} # track_id -> frame_idx

    def _build_class_mapping(self):
        """
        Dynamically extracts class IDs for traffic-relevant categories:
        car, motorcycle, bus, truck, bicycle.
        Does not assume hardcoded class IDs blindly.
        """
        target_categories = {
            'car': 'car',
            'motorcycle': 'motorcycle',
            'bike': 'motorcycle',
            'bus': 'bus',
            'truck': 'truck',
            'bicycle': 'bicycle'
        }
        
        self.target_class_ids = []
        self.class_name_map = {}

        if hasattr(self.model, 'names') and isinstance(self.model.names, dict):
            for cls_id, raw_name in self.model.names.items():
                name_clean = str(raw_name).lower().strip()
                for target_key, standard_label in target_categories.items():
                    if target_key in name_clean:
                        self.target_class_ids.append(int(cls_id))
                        self.class_name_map[int(cls_id)] = standard_label
                        break
        else:
            # Fallback default COCO mapping
            self.target_class_ids = [1, 2, 3, 5, 7]
            self.class_name_map = {1: 'bicycle', 2: 'car', 3: 'motorcycle', 5: 'bus', 7: 'truck'}

    def set_config(self, model_name=None, conf=None, imgsz=None):
        if model_name and model_name != self.model_name:
            self.model_name = model_name
            self.model, self.device = get_yolo_model(self.model_name, self.device_pref)
            self._build_class_mapping()
        if conf is not None:
            self.conf = float(conf)
        if imgsz is not None:
            self.imgsz = int(imgsz)

    def reset(self):
        self.track_history.clear()
        self.last_seen_frame.clear()

    def track(self, frame, frame_idx=0):
        """
        Runs ByteTrack persistent tracking with Ultralytics YOLO.
        Returns:
            detections: list of dicts with bounding boxes, IDs, centroids, history
            inference_ms: measured inference time in milliseconds
            device_str: 'CUDA' or 'CPU'
        """
        inference_ms = 0.0
        detections = []

        try:
            results = self.model.track(
                frame,
                persist=True,
                tracker=self.tracker_cfg,
                classes=self.target_class_ids,
                conf=self.conf,
                imgsz=self.imgsz,
                device=self.device,
                verbose=False
            )
        except Exception as e:
            print(f"[YoloTracker] Inference error: {e}")
            return [], 0.0, self.device.upper()

        if len(results) > 0:
            result = results[0]
            if hasattr(result, 'speed') and isinstance(result.speed, dict):
                inference_ms = float(result.speed.get('inference', 0.0))

            if result.boxes is not None and result.boxes.id is not None:
                boxes = result.boxes.xyxy.cpu().numpy()
                track_ids = result.boxes.id.int().cpu().numpy()
                classes = result.boxes.cls.int().cpu().numpy()
                confs = result.boxes.conf.cpu().numpy()

                for box, track_id, cls_id, conf in zip(boxes, track_ids, classes, confs):
                    x1, y1, x2, y2 = map(int, box)
                    class_name = self.class_name_map.get(int(cls_id), 'vehicle')
                    centroid = ((x1 + x2) // 2, (y1 + y2) // 2)
                    track_id = int(track_id)

                    if track_id not in self.track_history:
                        self.track_history[track_id] = []
                    self.track_history[track_id].append(centroid)
                    self.last_seen_frame[track_id] = frame_idx

                    # Maintain up to 30 past points for trajectory trail
                    if len(self.track_history[track_id]) > 30:
                        self.track_history[track_id].pop(0)

                    detections.append({
                        "class_name": class_name,
                        "track_id": track_id,
                        "confidence": round(float(conf), 2),
                        "x1": x1,
                        "y1": y1,
                        "x2": x2,
                        "y2": y2,
                        "centroid": centroid,
                        "history": list(self.track_history[track_id]),
                        "last_seen": frame_idx
                    })

        return detections, inference_ms, self.device.upper()
