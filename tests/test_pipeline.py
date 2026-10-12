import unittest
import sys
import os
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from camera.tracker import YoloTracker
from camera.vehicle_counter import VehicleCounter
from services.forecasting_service import TrafficForecastingService
from app import app

class TrafficPipelineTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def test_health_endpoint(self):
        res = self.app.get('/api/health')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("status"), "ok")
        self.assertIn("device", data)

    def test_videos_list_endpoint(self):
        res = self.app.get('/api/videos')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("videos", data)
        self.assertIn("highway.mp4", data["videos"])

    def test_sensors_endpoint_isolated(self):
        res = self.app.get('/api/sensors/status')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("is_simulated"))
        self.assertIn("SIMULATED SENSOR", data.get("label"))

    def test_vehicle_counter_cross_product_geometry(self):
        counter = VehicleCounter()
        # Line from (0, 360) to (1280, 360)
        counter.norm_pt1 = [0.0, 0.5]
        counter.norm_pt2 = [1.0, 0.5]
        counter.update_pixel_coords(1280, 720)

        # Vehicle moving DOWN (Direction B): from y=340 to y=380
        det1 = {
            "track_id": 101,
            "class_name": "car",
            "history": [(500, 340), (500, 380)]
        }
        res1 = counter.update_counts([det1], frame_idx=1, video_time_sec=1.0)
        self.assertEqual(res1["total_crossings"], 1)
        self.assertEqual(counter.direction_b_counts["total"], 1)
        self.assertEqual(counter.direction_a_counts["total"], 0)

        # Ensure NO duplicate counting on subsequent frame
        det1_next = {
            "track_id": 101,
            "class_name": "car",
            "history": [(500, 380), (500, 420)]
        }
        res1_next = counter.update_counts([det1_next], frame_idx=2, video_time_sec=2.0)
        self.assertEqual(res1_next["total_crossings"], 1) # Still 1!

        # Vehicle moving UP (Direction A): from y=390 to y=330
        det2 = {
            "track_id": 202,
            "class_name": "truck",
            "history": [(700, 390), (700, 330)]
        }
        res2 = counter.update_counts([det2], frame_idx=3, video_time_sec=3.0)
        self.assertEqual(res2["total_crossings"], 2)
        self.assertEqual(counter.direction_a_counts["total"], 1)
        self.assertEqual(counter.direction_a_counts["truck"], 1)

    def test_direction_reversal_toggle(self):
        counter = VehicleCounter()
        counter.norm_pt1 = [0.0, 0.5]
        counter.norm_pt2 = [1.0, 0.5]
        counter.update_pixel_coords(1280, 720)
        counter.reverse_directions = True

        # Moving DOWN (originally B, now A due to reversal)
        det = {
            "track_id": 303,
            "class_name": "bus",
            "history": [(500, 340), (500, 380)]
        }
        counter.update_counts([det], frame_idx=1, video_time_sec=1.0)
        self.assertEqual(counter.direction_a_counts["total"], 1)
        self.assertEqual(counter.direction_b_counts["total"], 0)

    def test_forecasting_service_short_clip_caveat(self):
        forecaster = TrafficForecastingService(window_sec=5.0)
        # Simulate 15 seconds of video observations
        forecaster.process_frame_state(
            video_time_sec=2.0,
            new_crossings=[{"direction": "A", "class_name": "car"}],
            visible_count=1,
            occupancy_proxy=5.0,
            avg_speed=40.0
        )
        forecaster.process_frame_state(
            video_time_sec=8.0,
            new_crossings=[{"direction": "B", "class_name": "truck"}],
            visible_count=2,
            occupancy_proxy=8.0,
            avg_speed=38.0
        )
        forecast = forecaster.generate_forecast(video_time_sec=12.0)
        self.assertEqual(forecast["confidence"], "Low")
        self.assertEqual(forecast["status"], "Preliminary")
        self.assertTrue(forecast["is_preliminary"])
        self.assertIn("Short observation window", forecast["explanation"])
        self.assertGreater(forecast["forecast_1min"], 0)
        self.assertGreater(forecast["forecast_5min"], 0)

if __name__ == '__main__':
    unittest.main()
