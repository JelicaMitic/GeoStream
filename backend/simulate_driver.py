import requests
import time
import random
import argparse

BASE_URL = "http://127.0.0.1:8000"

def simulate(driver_id: int, start_lat: float, start_lon: float):
    lat = start_lat
    lon = start_lon
    print(f"Pokrećem simulaciju za vozača {driver_id}...")

    while True:
        lat += random.uniform(-0.001, 0.001)
        lon += random.uniform(-0.001, 0.001)

        try:
            response = requests.post(f"{BASE_URL}/drivers/location", json={
                "driver_id": driver_id,
                "latitude": round(lat, 6),
                "longitude": round(lon, 6)
            })
            print(f"Vozač {driver_id} → lat: {lat:.6f}, lon: {lon:.6f} | status: {response.status_code}")
        except Exception as e:
            print(f"Greška: {e}")

        time.sleep(5)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--driver", type=int, required=True)
    parser.add_argument("--lat", type=float, default=44.8176)
    parser.add_argument("--lon", type=float, default=20.4569)
    args = parser.parse_args()

    simulate(args.driver, args.lat, args.lon)