"""
Simulira vozača koji putuje od Beograda prema Novom Sadu.
Šalje POST /drivers/location na instancu 1 (port 8001).

Pokreni pre ovoga dve backend instance:
  Terminal 1: cd backend && uvicorn app.main:app --port 8001 --reload
  Terminal 2: cd backend && uvicorn app.main:app --port 8002 --reload

Otvori dva browser taba:
  http://localhost:3000?port=8001
  http://localhost:3000?port=8002

Oba taba treba da vide marker kako se kreće — event putuje:
  POST /location → Instance 1 → Kafka → Instance 1 + Instance 2 consumer → oba WS broadcast-uju
"""

import requests
import time
import sys

TARGET_INSTANCE = "http://localhost:8001"
DRIVER_ID = int(sys.argv[1]) if len(sys.argv) > 1 else 1
STEPS = 30
INTERVAL_SEC = 1.5

# Beograd → Novi Sad (aproksimativna ruta)
ROUTE = [
    (44.8176, 20.4569),
    (44.8312, 20.4201),
    (44.8490, 20.3750),
    (44.8735, 20.3141),
    (44.9021, 20.2489),
    (44.9380, 20.1901),
    (44.9780, 20.1350),
    (45.0210, 20.0890),
    (45.0680, 20.0421),
    (45.1150, 20.0010),
    (45.1620, 19.9601),
    (45.2100, 19.9201),
    (45.2460, 19.8820),
    (45.2671, 19.8335),
]

def interpolate(route, steps):
    points = []
    segments = len(route) - 1
    per_seg = max(1, steps // segments)
    for i in range(segments):
        lat1, lon1 = route[i]
        lat2, lon2 = route[i + 1]
        for j in range(per_seg):
            t = j / per_seg
            points.append((lat1 + (lat2 - lat1) * t, lon1 + (lon2 - lon1) * t))
    points.append(route[-1])
    return points[:steps]

points = interpolate(ROUTE, STEPS)

print(f"Simulacija vozača {DRIVER_ID} — {len(points)} koraka, interval {INTERVAL_SEC}s")
print(f"Šaljem na: {TARGET_INSTANCE}\n")

for i, (lat, lon) in enumerate(points, 1):
    try:
        r = requests.post(
            f"{TARGET_INSTANCE}/drivers/location",
            json={"driver_id": DRIVER_ID, "latitude": round(lat, 6), "longitude": round(lon, 6)},
            timeout=3,
        )
        status = "OK" if r.status_code == 200 else f"ERR {r.status_code}"
        print(f"[{i:02d}/{len(points)}] {lat:.4f}, {lon:.4f}  →  {status}")
    except Exception as e:
        print(f"[{i:02d}/{len(points)}] Greška: {e}")
    time.sleep(INTERVAL_SEC)

print("\nSimulacija završena.")
