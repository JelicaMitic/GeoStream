from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app import models, schemas
from app.schemas import LocationUpdate
from app.logger import logger
from fastapi import APIRouter, Depends, HTTPException, Request

router = APIRouter(prefix="/drivers", tags=["drivers"])

@router.post("/location")
async def update_location(data: LocationUpdate, request: Request, db: Session = Depends(get_db)):
    try:
        driver = db.query(models.Driver).filter(models.Driver.id == data.driver_id).first()

        if not driver:
            logger.warning(f"Vozač {data.driver_id} nije pronađen")
            raise HTTPException(status_code=404, detail="Vozač nije pronađen")

        driver.status = "active"

        db.execute(text("""
            INSERT INTO location_events (driver_id, latitude, longitude, timestamp, geo_location)
            VALUES (:driver_id, :latitude, :longitude, NOW(),
                    ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326))
        """), {
            "driver_id": data.driver_id,
            "latitude": data.latitude,
            "longitude": data.longitude
        })
        db.commit()

        await request.app.state.manager.broadcast({
            "driver_id": data.driver_id,
            "driver_name": driver.name,
            "latitude": data.latitude,
            "longitude": data.longitude
        })

        logger.info(f"Vozač {data.driver_id} → lat: {data.latitude}, lon: {data.longitude}")
        return {"message": "Lokacija upisana"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Greška pri upisu lokacije: {e}")
        raise HTTPException(status_code=500, detail="Interna greška servera")

@router.get("/nearest")
def get_nearest_driver(lat: float, lon: float, db: Session = Depends(get_db)):
    try:
        result = db.execute(text("""
            SELECT 
                d.id,
                d.name,
                ST_Distance(
                    l.geo_location::geography,
                    ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography
                ) AS distance_meters
            FROM drivers d
            JOIN location_events l ON l.driver_id = d.id
            WHERE d.status = 'active'
            AND l.timestamp = (
                SELECT MAX(timestamp) 
                FROM location_events 
                WHERE driver_id = d.id
            )
            ORDER BY distance_meters
            LIMIT 1
        """), {"lat": lat, "lon": lon}).fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="Nema aktivnih vozača")

        logger.info(f"Najbliži vozač: {result.id}, rastojanje: {result.distance_meters:.0f}m")
        return {
            "driver_id": result.id,
            "driver_name": result.name,
            "distance_km": round(result.distance_meters / 1000, 2)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Greška pri traženju najbližeg vozača: {e}")
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

        locations = (
            db.query(models.LocationEvent)
            .filter(models.LocationEvent.driver_id == driver_id)
            .order_by(models.LocationEvent.timestamp.desc())
            .all()
        )

        logger.info(f"Istorija za vozača {driver_id}: {len(locations)} lokacija")
        return locations

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Greška pri dohvatanju istorije: {e}")
        raise HTTPException(status_code=500, detail="Interna greška servera")