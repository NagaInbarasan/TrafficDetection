import cv2

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
