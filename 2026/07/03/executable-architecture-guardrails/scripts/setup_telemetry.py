#!/usr/bin/env python3
"""setup_telemetry.py - Golden-path OpenTelemetry instrumentation for Python services."""

import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader


def setup_telemetry(app=None):
    trace_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    metric_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")

    trace_provider = TracerProvider()
    trace_exporter = OTLPSpanExporter(endpoint=trace_endpoint)
    trace_provider.add_span_processor(BatchSpanProcessor(trace_exporter))
    trace.set_tracer_provider(trace_provider)

    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=metric_endpoint),
        export_interval_millis=60000,
    )
    meter_provider = MeterProvider(metric_readers=[metric_reader])

    if app is not None:
        FlaskInstrumentor().instrument_app(app)
        RequestsInstrumentor().instrument()

    meter = meter_provider.get_meter(__name__)
    request_counter = meter.create_counter(
        "http.requests",
        description="Count of HTTP requests",
    )
    error_counter = meter.create_counter(
        "http.errors",
        description="Count of HTTP error responses",
    )
    latency_histogram = meter.create_histogram(
        "http.request.duration",
        unit="ms",
        description="HTTP request latency",
    )

    return {
        "meter": meter,
        "request_counter": request_counter,
        "error_counter": error_counter,
        "latency_histogram": latency_histogram,
    }


if __name__ == "__main__":
    print("Telemetry initialized. Import and call setup_telemetry(app) in your service.")
