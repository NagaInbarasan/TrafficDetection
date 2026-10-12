import joblib
import os
import pandas as pd
from datetime import datetime

class Predictor:
    def __init__(self):
        self.reg_model_path = 'ml/flow_model.pkl'
        self.clf_model_path = 'ml/congestion_model.pkl'
        self.reg_model = None
        self.clf_model = None
        
        if os.path.exists(self.reg_model_path) and os.path.exists(self.clf_model_path):
            self.reg_model = joblib.load(self.reg_model_path)
            self.clf_model = joblib.load(self.clf_model_path)
            
    def predict(self, current_data):
        if not self.reg_model or not self.clf_model:
            return None
            
        now = datetime.now()
        hour = now.hour
        day_of_week = now.weekday()
        is_peak = 1 if (7 <= hour <= 9) or (16 <= hour <= 19) else 0
        
        # Prepare feature array
        features = pd.DataFrame([{
            'direction_a_count': current_data.get('direction_a_count', 0),
            'direction_b_count': current_data.get('direction_b_count', 0),
            'direction_a_cars': current_data.get('direction_a_cars', 0),
            'direction_a_bikes': current_data.get('direction_a_bikes', 0),
            'direction_a_buses': current_data.get('direction_a_buses', 0),
            'direction_a_trucks': current_data.get('direction_a_trucks', 0),
            'direction_b_cars': current_data.get('direction_b_cars', 0),
            'direction_b_bikes': current_data.get('direction_b_bikes', 0),
            'direction_b_buses': current_data.get('direction_b_buses', 0),
            'direction_b_trucks': current_data.get('direction_b_trucks', 0),
            'average_estimated_speed': current_data.get('average_speed', 30.0),
            'traffic_density': current_data.get('traffic_density', 0.0),
            'hour': hour,
            'day_of_week': day_of_week,
            'is_peak': is_peak
        }])
        
        pred_flow = int(self.reg_model.predict(features)[0])
        pred_class_idx = int(self.clf_model.predict(features)[0])
        
        classes = ["LOW", "MEDIUM", "HIGH"]
        
        return {
            "predicted_vehicle_count": pred_flow,
            "predicted_direction_a_flow": int(pred_flow * 0.5), # Approx
            "predicted_direction_b_flow": int(pred_flow * 0.5),
            "predicted_density": min(100.0, pred_flow * 0.8),
            "congestion_level": classes[pred_class_idx],
            "prediction_horizon": "10 minutes"
        }
