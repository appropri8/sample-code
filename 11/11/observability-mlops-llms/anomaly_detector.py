"""Standalone anomaly detector script"""

from src import AnomalyDetector

if __name__ == "__main__":
    detector = AnomalyDetector()
    anomalies = detector.check_anomalies()
    
    if anomalies:
        detector.alert(anomalies)
    else:
        print("No anomalies detected.")

