from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.schemas import LocationUpdate
from app.logger import logger
import math

router = APIRouter(prefix="/drivers", tags=["drivers"])

@router.post("/location")
def update_location(data: LocationUpdate, db: Session = Depends(get_db)):
    try:
        driver = db.query(models.Driver).filter(models.Driver.id == data.driver_id).first()

        if not driver:
            logger.warning(f"Vozač {data.driver_id} nije pronađen")
            raise HTTPException(status_code=404, detail="Vozač nije pronađen")

        driver.status = "active"

        event = models.LocationEvent(
            driver_id=data.driver_id,
            latitude=data.latitude,
            longitude=data.longitude
        )
        db.add(event)
        db.commit()

        logger.info(f"Vozač {data.driver_id} → lat: {data.latitude}, lon: {data.longitude}")
        return {"message": "Lokacija upisana"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Greška pri upisu lokacije: {e}")
        raise HTTPException(status_code=500, detail="Interna greška servera")

@router.get("/active")
def get_active_drivers(db: Session = Depends(get_db)):
    try:
        drivers = db.query(models.Driver).filter(models.Driver.status == "active").all()
        logger.info(f"Aktivni vozači: {len(drivers)}")
        return drivers
    except Exception as e:
        logger.error(f"Greška pri dohvatanju vozača: {e}")
        raise HTTPException(status_code=500, detail="Interna greška servera")

@router.get("/{driver_id}/history")
def get_driver_history(driver_id: int, db: Session = Depends(get_db)):
    try:
        driver = db.query(models.Driver).filter(models.Driver.id == driver_id).first()

        if not driver:
            logger.warning(f"Istorija: vozač {driver_id} nije pronađen")
            raise HTTPException(status_code=404, detail="Vozač nije pronađen")

        logger.info(f"Istorija za vozača {driver_id}: {len(driver.locations)} lokacija")
        return driver.locations
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Greška pri dohvatanju istorije: {e}")
        raise HTTPException(status_code=500, detail="Interna greška servera")

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # poluprečnik Zemlje u km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))

@router.get("/nearest")
def get_nearest_driver(lat: float, lon: float, db: Session = Depends(get_db)):
    try:
        drivers = db.query(models.Driver).filter(models.Driver.status == "active").all()

        if not drivers:
            logger.warning("Nema aktivnih vozača")
            raise HTTPException(status_code=404, detail="Nema aktivnih vozača")

        nearest = None
        min_distance = float("inf")

        for driver in drivers:
            last_location = (
                db.query(models.LocationEvent)
                .filter(models.LocationEvent.driver_id == driver.id)
                .order_by(models.LocationEvent.timestamp.desc())
                .first()
            )

            if not last_location:
                continue

            distance = haversine(lat, lon, last_location.latitude, last_location.longitude)

            if distance < min_distance:
                min_distance = distance
                nearest = driver

        if not nearest:
            raise HTTPException(status_code=404, detail="Nema vozača sa poznatom lokacijom")

        logger.info(f"Najbliži vozač: {nearest.id}, rastojanje: {min_distance:.2f} km")
        return {
            "driver_id": nearest.id,
            "driver_name": nearest.name,
            "distance_km": round(min_distance, 2)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Greška pri traženju najbližeg vozača: {e}")
        raise HTTPException(status_code=500, detail="Interna greška servera")