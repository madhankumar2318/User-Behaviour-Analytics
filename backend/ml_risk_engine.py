"""
Machine Learning Risk Engine
Uses Isolation Forest for anomaly detection in user behavior
"""

from sklearn.ensemble import IsolationForest
import numpy as np
import joblib
import os
from datetime import datetime


class MLRiskEngine:
    def __init__(self, model_path='risk_model.pkl'):
        self.model_path = model_path
        self.model = IsolationForest(
            contamination=0.15,  # Expect 15% anomalies
            random_state=42,
            n_estimators=100
        )
        self.is_trained = False
        self.feature_names = [
            'login_hour',
            'login_minute',
            'downloads',
            'failed_attempts',
            'location_encoded'
        ]
        self.location_encoder = {}
        self.load_model()
    
    def load_model(self):
        """Load pre-trained model if exists"""
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                self.is_trained = True
                print("✅ ML model loaded successfully")
            except Exception as e:
                print(f"⚠️ Could not load model: {e}")
                self.is_trained = False
        else:
            print("ℹ️ No pre-trained model found. Will train on first use.")
    
    def save_model(self):
        """Save trained model to disk"""
        try:
            joblib.dump(self.model, self.model_path)
            print(f"✅ Model saved to {self.model_path}")
        except Exception as e:
            print(f"❌ Error saving model: {e}")
    
    def encode_location(self, location):
        """Encode location as numeric value"""
        if location not in self.location_encoder:
            self.location_encoder[location] = len(self.location_encoder)
        return self.location_encoder[location]
    
    def time_to_features(self, time_str):
        """Convert time string to hour and minute"""
        try:
            parts = time_str.split(':')
            hour = int(parts[0])
            minute = int(parts[1]) if len(parts) > 1 else 0
            return hour, minute
        except:
            return 12, 0  # Default to noon if parsing fails
    
    def extract_features(self, logs):
        """Extract ML features from logs"""
        features = []
        
        for log in logs:
            hour, minute = self.time_to_features(log.get('login_time', '12:00'))
            
            feature_vector = [
                hour,
                minute,
                log.get('downloads', 0),
                log.get('failed_attempts', 0),
                self.encode_location(log.get('location', 'Unknown'))
            ]
            features.append(feature_vector)
        
        return np.array(features)
    
    def train(self, logs):
        """Train model on historical data"""
        if len(logs) < 10:
            print(f"⚠️ Not enough data to train. Need at least 10 logs, got {len(logs)}")
            return False
        
        try:
            features = self.extract_features(logs)
            self.model.fit(features)
            self.is_trained = True
            self.save_model()
            print(f"✅ Model trained on {len(logs)} logs")
            return True
        except Exception as e:
            print(f"❌ Error training model: {e}")
            return False
    
    def predict_anomaly(self, log):
        """
        Predict if log is anomalous
        Returns: (anomaly_score, is_anomaly, confidence)
        """
        if not self.is_trained:
            return 0.0, False, 0.0
        
        try:
            features = self.extract_features([log])
            
            # Get anomaly score (negative = more anomalous)
            score = self.model.decision_function(features)[0]
            
            # Predict if anomaly (-1 = anomaly, 1 = normal)
            prediction = self.model.predict(features)[0]
            is_anomaly = (prediction == -1)
            
            # Convert score to 0-100 scale (more positive = more anomalous)
            # Normalize score to roughly 0-100 range
            normalized_score = max(0, min(100, (-score * 50) + 50))
            
            # Confidence based on how far from decision boundary
            confidence = min(100, abs(score) * 50)
            
            return normalized_score, is_anomaly, confidence
            
        except Exception as e:
            print(f"❌ Error predicting anomaly: {e}")
            return 0.0, False, 0.0
    
    def get_model_stats(self):
        """Get model statistics"""
        return {
            'is_trained': self.is_trained,
            'model_type': 'Isolation Forest',
            'contamination': 0.15,
            'n_estimators': 100,
            'locations_encoded': len(self.location_encoder)
        }


# Global instance
ml_engine = MLRiskEngine()


if __name__ == "__main__":
    # Test the ML engine
    print("Testing ML Risk Engine...")
    
    # Sample data
    sample_logs = [
        {'login_time': '09:30', 'downloads': 5, 'failed_attempts': 0, 'location': 'New York'},
        {'login_time': '10:15', 'downloads': 7, 'failed_attempts': 0, 'location': 'New York'},
        {'login_time': '14:20', 'downloads': 12, 'failed_attempts': 1, 'location': 'London'},
        {'login_time': '23:45', 'downloads': 25, 'failed_attempts': 3, 'location': 'Tokyo'},
        {'login_time': '02:30', 'downloads': 30, 'failed_attempts': 5, 'location': 'Singapore'},
        {'login_time': '11:00', 'downloads': 8, 'failed_attempts': 0, 'location': 'Mumbai'},
        {'login_time': '16:45', 'downloads': 20, 'failed_attempts': 2, 'location': 'Berlin'},
        {'login_time': '09:00', 'downloads': 6, 'failed_attempts': 0, 'location': 'New York'},
        {'login_time': '10:30', 'downloads': 9, 'failed_attempts': 0, 'location': 'London'},
        {'login_time': '15:00', 'downloads': 11, 'failed_attempts': 1, 'location': 'Paris'},
    ]
    
    # Train
    ml_engine.train(sample_logs)
    
    # Test prediction
    test_log = {'login_time': '03:00', 'downloads': 50, 'failed_attempts': 8, 'location': 'Unknown'}
    score, is_anomaly, confidence = ml_engine.predict_anomaly(test_log)
    
    print(f"\nTest Log: {test_log}")
    print(f"Anomaly Score: {score:.2f}")
    print(f"Is Anomaly: {is_anomaly}")
    print(f"Confidence: {confidence:.2f}%")
    
    print(f"\nModel Stats: {ml_engine.get_model_stats()}")
