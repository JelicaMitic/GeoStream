from kafka import KafkaProducer
import json
import os
from app.logger import logger

_producer = None

def get_producer():
    global _producer
    if _producer is None:
        bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        _producer = KafkaProducer(
            bootstrap_servers=bootstrap,
            value_serializer=lambda v: json.dumps(v).encode("utf-8")
        )
    return _producer

def send_location_event(driver_id: int, latitude: float, longitude: float, driver_name: str):
    try:
        producer = get_producer()
        event = {
            "driver_id": driver_id,
            "driver_name": driver_name,
            "latitude": latitude,
            "longitude": longitude
        }
        producer.send("driver-locations", value=event)
        producer.flush()
        logger.info(f"Kafka event poslat: vozač {driver_id} → {latitude}, {longitude}")
    except Exception as e:
        logger.warning(f"Kafka nije dostupna, event preskočen: {e}")
