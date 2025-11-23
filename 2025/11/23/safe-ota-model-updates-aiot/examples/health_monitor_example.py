"""Example: Health monitoring and rollback."""

import time
from src.health_monitor import HealthMonitor

def main():
    """Run health monitor example."""
    monitor = HealthMonitor()
    
    # Simulate some inferences
    print("Simulating inferences...")
    for i in range(10):
        # Simulate normal inference
        latency = 45.0 + (i * 2)  # Gradually increasing latency
        success = True
        monitor.record_inference(latency, success)
        time.sleep(0.1)
    
    # Get current metrics
    metrics = monitor.get_current_metrics()
    print(f"\nCurrent metrics:")
    print(f"  Average latency: {metrics['avg_latency_ms']:.2f}ms")
    print(f"  CPU usage: {metrics['cpu_percent']:.1f}%")
    print(f"  RAM usage: {metrics['ram_percent']:.1f}%")
    print(f"  Error rate: {metrics['error_rate']:.2%}")
    print(f"  Total inferences: {metrics['num_inferences']}")
    
    # Check health with thresholds
    thresholds = {
        "max_cpu_percent": 80,
        "max_ram_percent": 90,
        "max_latency_ms": 200,
        "max_error_rate": 0.01
    }
    
    is_healthy = monitor.check_health(metrics, thresholds)
    print(f"\nHealth check: {'✓ Healthy' if is_healthy else '✗ Unhealthy'}")
    
    # Simulate high CPU usage
    print("\nSimulating high CPU usage scenario...")
    # In real scenario, this would come from actual system metrics
    # For demo, we'll just check with modified metrics
    high_cpu_metrics = metrics.copy()
    high_cpu_metrics["cpu_percent"] = 85.0  # Exceeds threshold
    
    is_healthy_high_cpu = monitor.check_health(high_cpu_metrics, thresholds)
    print(f"Health check with high CPU: {'✓ Healthy' if is_healthy_high_cpu else '✗ Unhealthy (would trigger rollback)'}")

if __name__ == "__main__":
    main()

