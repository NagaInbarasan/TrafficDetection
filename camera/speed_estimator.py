import math

class SpeedEstimator:
    """
    Relative speed estimator based on centroid displacement over time.
    Without homography or camera calibration, pixel velocity is an estimated proxy.
    """
    def __init__(self, fps=30.0):
        self.fps = fps if fps > 0 else 30.0
        self.track_speeds = {} # track_id -> estimated speed
        self.speed_history = []

    def reset(self, fps=30.0):
        self.fps = fps if fps > 0 else 30.0
        self.track_speeds.clear()
        self.speed_history.clear()

    def estimate_speeds(self, detections):
        current_speeds = []

        for det in detections:
            track_id = det["track_id"]
            history = det.get("history", [])

            if len(history) >= 4:
                # Displacement over last 4 frames
                p1 = history[-4]
                p2 = history[-1]
                dx = p2[0] - p1[0]
                dy = p2[1] - p1[1]
                dist_px = math.hypot(dx, dy)
                
                # Pixels per second
                px_per_sec = (dist_px / 3.0) * self.fps

                # Relative proxy conversion factor (~0.08 scaling factor for standard road view)
                # Clearly documented as an uncalibrated relative estimate
                rel_speed = round(min(140.0, max(5.0, px_per_sec * 0.08)), 1)
                self.track_speeds[track_id] = rel_speed
                current_speeds.append(rel_speed)
                det["estimated_speed"] = rel_speed
            elif track_id in self.track_speeds:
                det["estimated_speed"] = self.track_speeds[track_id]
                current_speeds.append(self.track_speeds[track_id])
            else:
                det["estimated_speed"] = None

        avg_speed = round(sum(current_speeds) / len(current_speeds), 1) if current_speeds else 0.0

        return {
            "average_speed": avg_speed,
            "track_speeds": dict(self.track_speeds),
            "status": "uncalibrated_relative_estimate"
        }
