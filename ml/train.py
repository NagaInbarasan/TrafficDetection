import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score, accuracy_score, precision_score, recall_score, f1_score
import joblib
import json
import os
from ml.preprocess import preprocess_data, extract_features

def train_models():
    traffic_df = pd.read_csv('data/raw/traffic.csv')
    sensor_df = pd.read_csv('data/raw/sensors.csv')
    
    df = preprocess_data(traffic_df, sensor_df)
    X, y_reg, y_clf = extract_features(df)
    
    X_train, X_test, y_reg_train, y_reg_test, y_clf_train, y_clf_test = train_test_split(
        X, y_reg, y_clf, test_size=0.2, random_state=42
    )
    
    reg_model = RandomForestRegressor(n_estimators=50, random_state=42)
    reg_model.fit(X_train, y_reg_train)
    reg_preds = reg_model.predict(X_test)
    
    clf_model = RandomForestClassifier(n_estimators=50, random_state=42)
    clf_model.fit(X_train, y_clf_train)
    clf_preds = clf_model.predict(X_test)
    
    metrics = {
        "regression": {
            "mae": round(mean_absolute_error(y_reg_test, reg_preds), 2),
            "rmse": round(root_mean_squared_error(y_reg_test, reg_preds), 2),
            "r2": round(r2_score(y_reg_test, reg_preds), 2)
        },
        "classification": {
            "accuracy": round(accuracy_score(y_clf_test, clf_preds), 2),
            "precision": round(precision_score(y_clf_test, clf_preds, average='weighted', zero_division=0), 2),
            "recall": round(recall_score(y_clf_test, clf_preds, average='weighted', zero_division=0), 2),
            "f1": round(f1_score(y_clf_test, clf_preds, average='weighted', zero_division=0), 2)
        }
    }
    
    os.makedirs('ml', exist_ok=True)
    joblib.dump(reg_model, 'ml/flow_model.pkl')
    joblib.dump(clf_model, 'ml/congestion_model.pkl')
    
    with open('ml/metadata.json', 'w') as f:
        json.dump(metrics, f, indent=4)
        
    print("Models trained and saved successfully.")
    print("Metrics:", metrics)

if __name__ == '__main__':
    train_models()
