import pandas as pd
from datetime import datetime

def preprocess_data(traffic_df, sensor_df):
    traffic_df['timestamp'] = pd.to_datetime(traffic_df['timestamp'])
    sensor_df['timestamp'] = pd.to_datetime(sensor_df['timestamp'])
    
    # Merge on timestamp nearest
    df = pd.merge_asof(
        traffic_df.sort_values('timestamp'),
        sensor_df.sort_values('timestamp'),
        on='timestamp',
        direction='nearest',
        tolerance=pd.Timedelta('5min'),
        suffixes=('', '_sensor')
    )
    
    df.fillna(0, inplace=True)
    return df

def extract_features(df):
    df['hour'] = df['timestamp'].dt.hour
    df['day_of_week'] = df['timestamp'].dt.dayofweek
    df['is_peak'] = df['hour'].apply(lambda x: 1 if (7 <= x <= 9) or (16 <= x <= 19) else 0)
    
    # We predict future total vehicle count and congestion level
    df['future_total_flow'] = df['direction_a_count'].shift(-1) + df['direction_b_count'].shift(-1)
    df.dropna(inplace=True)
    
    def classify_congestion(row):
        total = row['future_total_flow']
        if total < 30: return 0 # LOW
        elif total < 70: return 1 # MEDIUM
        else: return 2 # HIGH
        
    df['future_congestion'] = df.apply(classify_congestion, axis=1)
    
    feature_cols = [
        'direction_a_count', 'direction_b_count',
        'direction_a_cars', 'direction_a_bikes', 'direction_a_buses', 'direction_a_trucks',
        'direction_b_cars', 'direction_b_bikes', 'direction_b_buses', 'direction_b_trucks',
        'average_estimated_speed', 'traffic_density',
        'hour', 'day_of_week', 'is_peak'
    ]
    
    X = df[feature_cols]
    y_reg = df['future_total_flow']
    y_clf = df['future_congestion']
    
    return X, y_reg, y_clf
