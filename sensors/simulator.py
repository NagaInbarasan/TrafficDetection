import random
from datetime import datetime

class SensorSimulator:
    def get_latest_reading(self):
        base_count = random.randint(20, 80)
        return {
            "timestamp": datetime.now().isoformat(),
            "sensor_name": "sim_sensor_1",
            "vehicle_count": base_count,
            "average_speed": round(random.uniform(20.0, 60.0), 2),
            "occupancy": round(random.uniform(10.0, 80.0), 2),
            "traffic_density": round(random.uniform(15.0, 85.0), 2)
        }
