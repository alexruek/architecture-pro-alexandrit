import os
import time
import random

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

OTEL_ENDPOINT = os.getenv("OTEL_COLLECTOR_ENDPOINT", "otel-collector:4317")

resource = Resource.create({SERVICE_NAME: "service-b"})
provider = TracerProvider(resource=resource)
exporter = OTLPSpanExporter(endpoint=OTEL_ENDPOINT, insecure=True)
provider.add_span_processor(BatchSpanProcessor(exporter))
trace.set_tracer_provider(provider)

tracer = trace.get_tracer(__name__)

app = FastAPI(title="Price Calculation Service")
FastAPIInstrumentor.instrument_app(app)


@app.get("/calculate")
def calculate_price():
    with tracer.start_as_current_span("calculate-price") as span:
        polygon_count = random.randint(1000, 50000)
        span.set_attribute("order.polygon_count", polygon_count)

        # simulate processing time proportional to model complexity
        time.sleep(0.1)

        price = round(polygon_count * 0.05, 2)
        span.set_attribute("order.calculated_price", price)
        span.set_attribute("order.currency", "RUB")

        return {
            "price": price,
            "polygon_count": polygon_count,
            "currency": "RUB",
        }


@app.get("/health")
def health():
    return {"status": "ok"}
