"""Full rollout with SLO monitoring"""
from datetime import datetime, timedelta
from typing import Dict, Any, List


class FullRollout:
    """Full rollout with SLO monitoring"""
    
    def __init__(
        self,
        workflow,
        slo_window_minutes: int = 60,
        slo_conditions: Dict[str, Any] = None
    ):
        self.workflow = workflow
        self.slo_window = timedelta(minutes=slo_window_minutes)
        self.slo_conditions = slo_conditions or {
            "error_rate": 0.01,  # 1%
            "p95_latency_ms": 5000,
            "availability": 0.99  # 99%
        }
        self.start_time = datetime.now()
        self.metrics: List[Dict[str, Any]] = []
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute workflow and record metrics"""
        start_time = datetime.now()
        
        try:
            result = self.workflow.execute(input_data)
            latency_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            self.metrics.append({
                "timestamp": datetime.now(),
                "success": True,
                "latency_ms": latency_ms,
                "error": None
            })
            
            return result
        except Exception as e:
            latency_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            self.metrics.append({
                "timestamp": datetime.now(),
                "success": False,
                "latency_ms": latency_ms,
                "error": str(e)
            })
            
            raise
    
    def check_slo(self) -> bool:
        """Check if SLOs are met"""
        if datetime.now() - self.start_time < self.slo_window:
            return False  # Not enough time
        
        # Calculate metrics from window
        window_start = datetime.now() - self.slo_window
        window_metrics = [
            m for m in self.metrics 
            if m["timestamp"] >= window_start
        ]
        
        if len(window_metrics) < 100:
            return False  # Not enough samples
        
        # Check error rate
        error_count = sum(1 for m in window_metrics if not m.get("success", True))
        error_rate = error_count / len(window_metrics)
        
        if error_rate > self.slo_conditions["error_rate"]:
            return False
        
        # Check latency
        latencies = [m["latency_ms"] for m in window_metrics]
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]
        
        if p95_latency > self.slo_conditions["p95_latency_ms"]:
            return False
        
        # Check availability
        total_requests = len(window_metrics)
        successful_requests = sum(1 for m in window_metrics if m.get("success", True))
        availability = successful_requests / total_requests if total_requests > 0 else 0
        
        if availability < self.slo_conditions["availability"]:
            return False
        
        return True
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get rollout metrics"""
        if not self.metrics:
            return {}
        
        window_start = datetime.now() - self.slo_window
        window_metrics = [
            m for m in self.metrics 
            if m["timestamp"] >= window_start
        ]
        
        if not window_metrics:
            return {}
        
        error_count = sum(1 for m in window_metrics if not m.get("success", True))
        latencies = [m["latency_ms"] for m in window_metrics]
        
        return {
            "total_requests": len(window_metrics),
            "error_count": error_count,
            "error_rate": error_count / len(window_metrics),
            "avg_latency_ms": sum(latencies) / len(latencies),
            "p95_latency_ms": sorted(latencies)[int(len(latencies) * 0.95)],
            "availability": sum(1 for m in window_metrics if m.get("success", True)) / len(window_metrics),
            "slo_met": self.check_slo()
        }

