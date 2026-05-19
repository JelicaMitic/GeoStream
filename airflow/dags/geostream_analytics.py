from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import psycopg2
import json
import os

default_args = {
    "owner": "geostream",
    "retries": 1,
    "retry_delay": timedelta(minutes=5)
}


def get_conn():
    return psycopg2.connect(
        host=os.environ.get("GEOSTREAM_DB_HOST", "host.docker.internal"),
        port=os.environ.get("GEOSTREAM_DB_PORT", 5432),
        dbname=os.environ.get("GEOSTREAM_DB_NAME", "geostream"),
        user=os.environ.get("GEOSTREAM_DB_USER", "postgres"),
        password=os.environ.get("GEOSTREAM_DB_PASSWORD", "")
    )

def rides_summary():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            COUNT(*) as total_rides,
            COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
            COUNT(CASE WHEN status = 'requested' THEN 1 END) as pending
        FROM rides
    """)
    row = cur.fetchone()
    print(f"Ukupno vožnji: {row[0]}, Završenih: {row[1]}, Na čekanju: {row[2]}")
    conn.close()

def active_drivers_summary():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT d.name, COUNT(l.id) as ping_count
        FROM drivers d
        LEFT JOIN location_events l ON l.driver_id = d.id
        WHERE l.timestamp > NOW() - INTERVAL '24 hours'
        GROUP BY d.name
        ORDER BY ping_count DESC
    """)
    rows = cur.fetchall()
    for row in rows:
        print(f"Vozač: {row[0]}, Pingova danas: {row[1]}")
    conn.close()

def location_events_summary():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) as total_events
        FROM location_events
        WHERE timestamp > NOW() - INTERVAL '24 hours'
    """)
    row = cur.fetchone()
    print(f"GPS eventi poslednjih 24h: {row[0]}")
    conn.close()

with DAG(
    dag_id="geostream_nightly_analytics",
    default_args=default_args,
    description="Nightly batch analitika GeoStream podataka",
    schedule="0 2 * * *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["geostream", "analytics"]
) as dag:

    t1 = PythonOperator(
        task_id="rides_summary",
        python_callable=rides_summary
    )

    t2 = PythonOperator(
        task_id="active_drivers_summary",
        python_callable=active_drivers_summary
    )

    t3 = PythonOperator(
        task_id="location_events_summary",
        python_callable=location_events_summary
    )

    t1 >> t2 >> t3