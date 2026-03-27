from faststream import FastStream
from faststream.kafka import KafkaBroker

from app.core.config import Settings


def create_kafka_broker(settings: Settings) -> KafkaBroker:
    return KafkaBroker(settings.kafka_bootstrap_servers)


def create_bus_app(settings: Settings) -> FastStream:
    broker = create_kafka_broker(settings)
    return FastStream(broker)
