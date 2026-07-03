"""
OpenTelemetry setup for cell-based observability.

This module shows how to tag traces, metrics, and logs
with tenant and cell identifiers for isolation monitoring.
"""

import time
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class CellTelemetry:
    """
    Telemetry data tagged with cell and tenant attributes.
    
    In production, use @opentelemetry/sdk-trace-node and
    @opentelemetry/exporter-trace-otlp-http.
    """
    cell_id: str
    tenant_id: Optional[str]
    region: str
    deployment_version: str
    trace_id: Optional[str] = None
    span_id: Optional[str] = None


class TelemetrySetup:
    """
    Configures OpenTelemetry with cell-aware resource attributes.
    
    The key is attaching these to every signal:
    - tenant.id
    - cell.id
    - cell.region
    - deployment.version
    """
    
    def __init__(
        self,
        service_name: str,
        cell_id: str,
        region: str,
        deployment_version: str,
    ):
        self.service_name = service_name
        self.cell_id = cell_id
        self.region = region
        self.deployment_version = deployment_version
        # In production, initialize real OTEL SDK
        self._spans: list[Dict[str, Any]] = []
        self._metrics: list[Dict[str, Any]] = []
    
    def create_span(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> CellTelemetry:
        """
        Create a span with cell/tenant attributes.
        
        Args:
            name: Span name
            attributes: Additional attributes
            
        Returns:
            CellTelemetry with trace context
        """
        base_attrs = {
            "service.name": self.service_name,
            "service.version": self.deployment_version,
            "cell.id": self.cell_id,
            "cell.region": self.region,
            "deployment.version": self.deployment_version,
        }
        if attributes:
            base_attrs.update(attributes)
        
        trace_id = f"trace-{time.time_ns()}"
        span_id = f"span-{time.time_ns() % 1000000}"
        
        span = {
            "name": name,
            "trace_id": trace_id,
            "span_id": span_id,
            "attributes": base_attrs,
            "timestamp": time.time(),
        }
        self._spans.append(span)
        
        return CellTelemetry(
            cell_id=self.cell_id,
            tenant_id=base_attrs.get("tenant.id"),
            region=self.region,
            deployment_version=self.deployment_version,
            trace_id=trace_id,
            span_id=span_id,
        )
    
    def record_request(self, method: str, path: str, status_code: int, duration_ms: int, tenant_id: Optional[str] = None) -> None:
        """Record a request metric with cell/tenant tags."""
        metric = {
            "name": "cell.requests.total",
            "attributes": {
                "cell.id": self.cell_id,
                "tenant.id": tenant_id or "unknown",
                "http.method": method,
                "http.route": path,
                "http.status_code": str(status_code),
            },
            "value": 1,
            "timestamp": time.time(),
        }
        self._metrics.append(metric)
    
    def record_latency(self, duration_ms: int, status_code: int) -> None:
        """Record request duration histogram."""
        metric = {
            "name": "cell.request.duration",
            "attributes": {
                "cell.id": self.cell_id,
                "http.status_code": str(status_code),
            },
            "value": duration_ms,
            "timestamp": time.time(),
        }
        self._metrics.append(metric)
    
    def get_spans(self) -> list[Dict[str, Any]]:
        """Get all recorded spans (for testing)."""
        return self._spans
    
    def get_metrics(self) -> list[Dict[str, Any]]:
        """Get all recorded metrics (for testing)."""
        return self._metrics


# Example usage
def setup_cell_telemetry(
    cell_id: str,
    region: str,
    deployment_version: str,
) -> TelemetrySetup:
    """
    Initialize telemetry for a cell.
    
    In production:
    
    const resource = new Resource({
      [SemanticResourceAttributes.SERVICE_NAME]: 'saas-platform',
      [SemanticResourceAttributes.SERVICE_VERSION]: deploymentVersion,
      'cell.id': cellId,
      'cell.region': region,
      'deployment.version': deploymentVersion,
    });
    """
    return TelemetrySetup(
        service_name="saas-platform",
        cell_id=cell_id,
        region=region,
        deployment_version=deployment_version,
    )


# Middleware for tracing requests
def create_trace_middleware(telemetry: TelemetrySetup):
    """
    Create middleware that traces every request.
    
    This attaches tenant.id and cell.id to each trace.
    """
    def middleware(request: Dict[str, Any], response: Dict[str, Any]) -> None:
        start_time = time.time()
        
        # Extract tenant from request
        tenant_id = (
            request.get("headers", {}).get("x-tenant-id")
            or request.get("tenant", {}).get("id")
        )
        
        # Create trace span
        telemetry.create_span(
            "handle-request",
            {
                "tenant.id": tenant_id or "unknown",
                "http.method": request.get("method", "GET"),
                "http.route": request.get("path", "/"),
            },
        )
        
        # Record metrics on response
        duration_ms = int((time.time() - start_time) * 1000)
        telemetry.record_request(
            request.get("method", "GET"),
            request.get("path", "/"),
            response.get("status_code", 200),
            duration_ms,
            tenant_id,
        )
        telemetry.record_latency(duration_ms, response.get("status_code", 200))
    
    return middleware