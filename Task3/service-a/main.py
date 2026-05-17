import os

import httpx
from fastapi import FastAPI, HTTPException
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

OTEL_ENDPOINT = os.getenv("OTEL_COLLECTOR_ENDPOINT", "otel-collector:4317")
SERVICE_B_URL = os.getenv("SERVICE_B_URL", "http://service-b:8080")

resource = Resource.create({SERVICE_NAME: "service-a"})
provider = TracerProvider(resource=resource)
exporter = OTLPSpanExporter(endpoint=OTEL_ENDPOINT, insecure=True)
provider.add_span_processor(BatchSpanProcessor(exporter))
trace.set_tracer_provider(provider)

# HTTPXClientInstrumentor automatically injects W3C TraceContext headers
# into every outgoing request, ensuring the trace continues in service-b
HTTPXClientInstrumentor().instrument()

tracer = trace.get_tracer(__name__)

app = FastAPI(title="Order Service")
FastAPIInstrumentor.instrument_app(app)


@app.get("/order")
def create_order():
    with tracer.start_as_current_span("create-order") as span:
        order_id = "ORD-12345"
        span.set_attribute("order.id", order_id)
        span.set_attribute("order.status", "SUBMITTED")

        try:
            with httpx.Client(timeout=15.0) as client:
                response = client.get(f"{SERVICE_B_URL}/calculate")
                response.raise_for_status()
                price_data = response.json()
        except httpx.HTTPError as exc:
            span.record_exception(exc)
            span.set_status(trace.StatusCode.ERROR, str(exc))
            raise HTTPException(
                status_code=502, detail="Price calculation service unavailable"
            )

        span.set_attribute("order.price", price_data.get("price", 0))
        span.set_attribute("order.status", "PRICE_CALCULATED")

        return {
            "order_id": order_id,
            "status": "PRICE_CALCULATED",
            "price": price_data.get("price"),
            "polygon_count": price_data.get("polygon_count"),
            "currency": price_data.get("currency"),
        }


@app.get("/health")
def health():
    return {"status": "ok"}
