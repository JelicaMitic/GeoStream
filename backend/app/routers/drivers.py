from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.schemas import LocationUpdate

router = APIRouter(prefix="/drivers", tags=["drivers"])

@router.post("/location")
def update_location(data: LocationUpdate, db: Session = Depends(get_db)):
    driver = db.query(models.Driver).filter(models.Driver.id == data.driver_id).first()
    
    if not driver:
        raise HTTPException(status_code=404, detail="Vozač nije pronađen")
    
    driver.status = "active"
    
    event = models.LocationEvent(
        driver_id=data.driver_id,
        latitude=data.latitude,
        longitude=data.longitude
    )
    db.add(event)
    db.commit()
    
    return {"message": "Lokacija upisana"}

@router.get("/active")
def get_active_drivers(db: Session = Depends(get_db)):
    drivers = db.query(models.Driver).filter(models.Driver.status == "active").all()
    return drivers

@router.get("/{driver_id}/history")
def get_driver_history(driver_id: int, db: Session = Depends(get_db)):
    driver = db.query(models.Driver).filter(models.Driver.id == driver_id).first()
    
    if not driver:
        raise HTTPException(status_code=404, detail="Vozač nije pronađen")
    
    return driver.locations