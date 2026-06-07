from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from kafka import KafkaConsumer
import json
import math
import os

default_args = {
    "owner": "geostream",
    "retries": 1,
    "retry_delay": timedelta(minutes=5)
}

KAFKA_BOOTSTRAP = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
TOPIC = "driver-locations"
GROUP_ID = "geostream-airflow-batch"


def haversine(lat1, lon1, lat2, lon2):
    """Rastojanje između dve GPS tačke u kilometrima."""
    R = 6371
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = math.sin(d_lat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


def consume_and_aggregate(**context):
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        group_id=GROUP_ID,
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        consumer_timeout_ms=10000, 
    )

    events_by_driver: dict[str, list] = {}
    total = 0

    for message in consumer:
        event = message.value
        driver_id = str(event.get("driver_id"))
        if driver_id not in events_by_driver:
            events_by_driver[driver_id] = []
        events_by_driver[driver_id].append(event)
        total += 1

    consumer.commit()
    consumer.close()

    print(f"Ukupno pročitanih Kafka poruka: {total}")

    if not events_by_driver:
        print("Nema novih poruka od poslednjeg pokretanja.")
        return

    # Agregacija po vozaču
    results = []
    for driver_id, events in events_by_driver.items():
        driver_name = events[0].get("driver_name", f"Vozač {driver_id}")
        total_km = 0.0

        for i in range(1, len(events)):
            prev = events[i - 1]
            curr = events[i]
            total_km += haversine(
                prev["latitude"], prev["longitude"],
                curr["latitude"], curr["longitude"]
            )

        results.append({
            "driver_id": driver_id,
            "driver_name": driver_name,
            "ping_count": len(events),
            "total_km": round(total_km, 3)
        })

    results.sort(key=lambda x: x["total_km"], reverse=True)

    print("=" * 45)
    print(f"{'Vozač':<20} {'Pingova':>8} {'Km':>10}")
    print("=" * 45)
    for r in results:
        print(f"{r['driver_name']:<20} {r['ping_count']:>8} {r['total_km']:>10.3f}")
    print("=" * 45)

    context["ti"].xcom_push(key="driver_stats", value=results)


def report_top_driver(**context):
    results = context["ti"].xcom_pull(key="driver_stats", task_ids="consume_kafka_locations")

    if not results:
        print("Nema podataka za izveštaj.")
        return

    top = results[0]
    print(f"Najaktivniji vozač: {top['driver_name']} sa {top['total_km']} km u ovom batch-u.")


with DAG(
    dag_id="kafka_location_batch",
    default_args=default_args,
    description="Batch obrada lokacija vozača iz Kafka topica",
    schedule="*/10 * * * *",  # svakih 10 minuta
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["geostream", "kafka", "batch"]
) as dag:

    t1 = PythonOperator(
        task_id="consume_kafka_locations",
        python_callable=consume_and_aggregate,
        provide_context=True,
    )

    t2 = PythonOperator(
        task_id="report_top_driver",
        python_callable=report_top_driver,
        provide_context=True,
    )

    t1 >> t2
