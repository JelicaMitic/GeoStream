from kafka import KafkaConsumer
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.logger import logger
from app.database import SessionLocal
from app import models

def start_consumer():
    consumer = KafkaConsumer(
        "driver-locations",
        bootstrap_servers="localhost:9092",
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        group_id="geostream-consumer",
        auto_offset_reset="earliest"
    )

    logger.info("Kafka consumer pokrenut, slušam driver-locations topic...")

    for message in consumer:
        event = message.value
        logger.info(f"Primljen event: vozač {event['driver_id']} → {event['latitude']}, {event['longitude']}")

        try:
            db = SessionLocal()
            driver = db.query(models.Driver).filter(models.Driver.id == event["driver_id"]).first()
            if driver:
                logger.info(f"Event procesiran za vozača: {driver.name}")
            db.close()
        except Exception as e:
            logger.error(f"Greška pri procesiranju eventa: {e}")

if __name__ == "__main__":
    start_consumer()