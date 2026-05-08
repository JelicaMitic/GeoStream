from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app import models
from app.schemas import RideRequest, RideResponse
from app.logger import logger
import math

router = APIRouter(prefix="/rides", tags=["rides"])

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))

@router.post("/request", response_model=RideResponse)
def request_ride(data: RideRequest, db: Session = Depends(get_db)):
    try:
        drivers = db.query(models.Driver).filter(models.Driver.status == "active").all()

        if not drivers:
            raise HTTPException(status_code=404, detail="Nema dostupnih vozača")

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

            distance = haversine(data.pickup_lat, data.pickup_lon, last_location.latitude, last_location.longitude)
            if distance < min_distance:
                min_distance = distance
                nearest = driver

        if not nearest:
            raise HTTPException(status_code=404, detail="Nema vozača sa poznatom lokacijom")

        ride = models.Ride(
            driver_id=nearest.id,
            passenger_name=data.passenger_name,
            status="requested",
            pickup_lat=data.pickup_lat,
            pickup_lon=data.pickup_lon
        )
        db.add(ride)
        nearest.status = "busy"
        db.commit()
        db.refresh(ride)

        logger.info(f"Vožnja {ride.id} kreirana - vozač: {nearest.id}, putnik: {data.passenger_name}")
        return ride

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Greška pri kreiranju vožnje: {e}")
        raise HTTPException(status_code=500, detail="Interna greška servera")

@router.post("/{ride_id}/start", response_model=RideResponse)
def start_ride(ride_id: int, db: Session = Depends(get_db)):
    try:
        ride = db.query(models.Ride).filter(models.Ride.id == ride_id).first()

        if not ride:
            raise HTTPException(status_code=404, detail="Vožnja nije pronađena")
        if ride.status != "requested":
            raise HTTPException(status_code=400, detail=f"Vožnja je već u statusu: {ride.status}")

        ride.status = "active"
        ride.started_at = datetime.utcnow()
        db.commit()
        db.refresh(ride)

        logger.info(f"Vožnja {ride_id} počela")
        return ride

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Greška pri pokretanju vožnje: {e}")
        raise HTTPException(status_code=500, detail="Interna greška servera")

@router.post("/{ride_id}/complete", response_model=RideResponse)
def complete_ride(ride_id: int, dropoff_lat: float, dropoff_lon: float, db: Session = Depends(get_db)):
    try:
        ride = db.query(models.Ride).filter(models.Ride.id == ride_id).first()

        if not ride:
            raise HTTPException(status_code=404, detail="Vožnja nije pronađena")
        if ride.status != "active":
            raise HTTPException(status_code=400, detail=f"Vožnja nije aktivna, status: {ride.status}")

        ride.status = "completed"
        ride.completed_at = datetime.utcnow()
        ride.dropoff_lat = dropoff_lat
        ride.dropoff_lon = dropoff_lon

        driver = db.query(models.Driver).filter(models.Driver.id == ride.driver_id).first()
        driver.status = "active"

        db.commit()
        db.refresh(ride)

        logger.info(f"Vožnja {ride_id} završena")
        return ride

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Greška pri završetku vožnje: {e}")
        raise HTTPException(status_code=500, detail="Interna greška servera")

@router.get("/{ride_id}", response_model=RideResponse)
def get_ride(ride_id: int, db: Session = Depends(get_db)):
    ride = db.query(models.Ride).filter(models.Ride.id == ride_id).first()
    if not ride:
        raise HTTPException(status_code=404, detail="Vožnja nije pronađena")
    return ride