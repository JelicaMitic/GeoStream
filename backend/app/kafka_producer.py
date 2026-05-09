from kafka import KafkaProducer
import json
from app.logger import logger

producer = None

def get_producer():
    global producer
    if producer is None:
        try:
            producer = KafkaProducer(
                bootstrap_servers="localhost:9092",
                value_serializer=lambda v: json.dumps(v).encode("utf-8")
            )
            logger.info("Kafka producer povezan")
        except Exception as e:
            logger.error(f"Kafka producer greška: {e}")
    return producer

def send_location_event(driver_id: int, latitude: float, longitude: float, driver_name: str):
    p = get_producer()
    if p is None:
        logger.warning("Kafka nije dostupna, preskačem event")
        return
    
    event = {
        "driver_id": driver_id,
        "driver_name": driver_name,
        "latitude": latitude,
        "longitude": longitude
    }
    
    p.send("driver-locations", value=event)
    p.flush()
    logger.info(f"Kafka event poslat za vozača {driver_id}")