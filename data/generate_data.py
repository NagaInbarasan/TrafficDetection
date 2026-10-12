import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

def generate_historical_data():
    np.random.seed(42)
    end_time = datetime.now()
    start_time = end_time - timedelta(days=30)
    
    timestamps = pd.date_range(start=start_time, end=end_time, freq='10min')
    
    traffic_data = []
    sensor_data = []
    
    for t in timestamps:
        hour = t.hour
        if 7 <= hour <= 9 or 16 <= hour <= 19:
            base_count = np.random.randint(50, 100)
            density = np.random.uniform(60, 95)
            speed = np.random.uniform(10, 30)
        elif 0 <= hour <= 5:
            base_count = np.random.randint(5, 20)
            density = np.random.uniform(5, 20)
            speed = np.random.uniform(50, 80)
        else:
            base_count = np.random.randint(20, 60)
            density = np.random.uniform(20, 60)
            speed = np.random.uniform(30, 60)
            
        dir_a = int(base_count * 0.6)
        dir_b = base_count - dir_a
        
        a_cars = int(dir_a * 0.6)
        a_bikes = int(dir_a * 0.25)
        a_buses = int(dir_a * 0.05)
        a_trucks = dir_a - a_cars - a_bikes - a_buses
        
        b_cars = int(dir_b * 0.6)
        b_bikes = int(dir_b * 0.25)
        b_buses = int(dir_b * 0.05)
        b_trucks = dir_b - b_cars - b_bikes - b_buses
        
        traffic_data.append([
            t, 'default', base_count, dir_a, dir_b,
            a_cars, a_bikes, a_buses, a_trucks,
            b_cars, b_bikes, b_buses, b_trucks,
            speed, density, density
        ])
        sensor_data.append([t, 'sensor_1', base_count + np.random.randint(-5, 6), speed + np.random.uniform(-5, 5), density + np.random.uniform(-2, 2), density + np.random.uniform(-2, 2)])
        
    cols = [
        'timestamp', 'video_session_id', 'visible_vehicle_count',
        'direction_a_count', 'direction_b_count',
        'direction_a_cars', 'direction_a_bikes', 'direction_a_buses', 'direction_a_trucks',
        'direction_b_cars', 'direction_b_bikes', 'direction_b_buses', 'direction_b_trucks',
        'average_estimated_speed', 'occupancy', 'traffic_density'
    ]
    df_traffic = pd.DataFrame(traffic_data, columns=cols)
    os.makedirs('data/raw', exist_ok=True)
    df_traffic.to_csv('data/raw/traffic.csv', index=False)
    
    df_sensor = pd.DataFrame(sensor_data, columns=['timestamp', 'sensor_name', 'vehicle_count', 'average_speed', 'occupancy', 'traffic_density'])
    df_sensor.to_csv('data/raw/sensors.csv', index=False)
    print("Historical data generated.")

if __name__ == '__main__':
    generate_historical_data()
