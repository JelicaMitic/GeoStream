import asyncio
import json
import os
import uuid
from kafka import KafkaConsumer
from app.logger import logger


def start_consumer_thread(loop, manager):
    bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    # Unique group ID per instance so every instance receives every message.
    # Without this, Kafka would load-balance messages across instances in the
    # same group, meaning only one instance would broadcast each event.
    group_id = f"geostream-ws-{uuid.uuid4()}"

    try:
        consumer = KafkaConsumer(
            "driver-locations",
            bootstrap_servers=bootstrap,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            group_id=group_id,
            auto_offset_reset="latest",
        )
        logger.info(f"Kafka consumer pokrenut (group: {group_id}, broker: {bootstrap})")

        for message in consumer:
            event = message.value
            logger.info(
                f"[Kafka] vozač {event['driver_id']} → {event['latitude']}, {event['longitude']}"
            )
            asyncio.run_coroutine_threadsafe(manager.broadcast(event), loop)

    except Exception as e:
        logger.error(f"Kafka consumer greška: {e}")
