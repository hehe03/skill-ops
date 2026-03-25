from typing import List, Dict


def detect_anomalies(features: List[Dict]) -> List[Dict]:
    # Lightweight anomaly detector based on latency distribution and error counts
    if not features:
        return []
    latencies = [f.get("latency_ms", 0) for f in features]
    mean = sum(latencies) / len(latencies) if latencies else 0
    std = (sum((x - mean) ** 2 for x in latencies) / len(latencies)) ** 0.5 if latencies else 0
    anomalies = []
    for f in features:
        lat = f.get("latency_ms", 0)
        if std > 0 and lat > mean + 2 * std:
            anomalies.append(f)
        elif f.get("errors", 0) > 0:
            anomalies.append(f)
    return anomalies
