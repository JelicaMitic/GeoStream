from kafka import KafkaConsumer
import json
import sys
import os
from collections import defaultdict
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.logger import logger
from app.database import SessionLocal
from app import models

# in-memory statistike
stats = {
    "total_events": 0,
    "events_per_driver": defaultdict(int),
    "last_seen": {},
    "driver_names": {}
}

def get_zone(lat, lon):
    if lat > 44.82:
        return "Severni Beograd"
    elif lat > 44.80:
        return "Centralni Beograd"
    else:
        return "Južni Beograd"

def print_stats():
    print("\n" + "="*50)
    print(f"REAL-TIME STATISTIKE — {datetime.now().strftime('%H:%M:%S')}")
    print("="*50)
    print(f"Ukupno eventi: {stats['total_events']}")
    for driver_id, count in stats["events_per_driver"].items():
        name = stats["driver_names"].get(driver_id, f"Vozač {driver_id}")
        last = stats["last_seen"].get(driver_id, {})
        zone = get_zone(last.get("lat", 0), last.get("lon", 0))
        print(f"  {name}: {count} pingova | zona: {zone} | pos: {last.get('lat', '?'):.4f}, {last.get('lon', '?'):.4f}")
    print("="*50 + "\n")

def start_consumer():
    consumer = KafkaConsumer(
        "driver-locations",
        bootstrap_servers="localhost:9092",
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        group_id="geostream-consumer-v2",
        auto_offset_reset="latest"
    )

    logger.info("Kafka consumer pokrenut, slušam driver-locations topic...")

    for message in consumer:
        event = message.value
        driver_id = event["driver_id"]

        stats["total_events"] += 1
        stats["events_per_driver"][driver_id] += 1
        stats["last_seen"][driver_id] = {
            "lat": event["latitude"],
            "lon": event["longitude"]
        }
        stats["driver_names"][driver_id] = event["driver_name"]

        try:
            db = SessionLocal()
            driver = db.query(models.Driver).filter(models.Driver.id == driver_id).first()
            if driver:
                logger.info(f"Event procesiran: {driver.name} → zona: {get_zone(event['latitude'], event['longitude'])}")
            db.close()
        except Exception as e:
            logger.error(f"Greška pri procesiranju eventa: {e}")

        if stats["total_events"] % 5 == 0:
            print_stats()

if __name__ == "__main__":
    start_consumer()