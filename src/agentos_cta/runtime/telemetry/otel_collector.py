# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# OpenTelemetry 收集器封装。

from typing import Dict, Any, Optional
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
import logging

logger = logging.getLogger(__name__)


class OTELCollector:
    """
    OpenTelemetry 收集器，负责初始化 tracer provider 和 exporter。
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.service_name = config.get("service_name", "agentos")
        self.endpoint = config.get("endpoint", "http://localhost:4317")
        self._provider = None

    def setup(self):
        """初始化 OpenTelemetry。"""
        resource = Resource(attributes={
            SERVICE_NAME: self.service_name
        })
        provider = TracerProvider(resource=resource)
        exporter = OTLPSpanExporter(endpoint=self.endpoint, insecure=True)
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)
        self._provider = provider
        logger.info(f"OTEL collector initialized, sending to {self.endpoint}")

    def get_tracer(self, name: str):
        """获取指定名称的 tracer。"""
        if not self._provider:
            self.setup()
        return trace.get_tracer(name)