from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional

class LocationUpdate(BaseModel):
    driver_id: int
    latitude: float
    longitude: float

    @field_validator("latitude")
    def validate_latitude(cls, v):
        if not -90 <= v <= 90:
            raise ValueError("Latitude mora biti između -90 i 90")
        return v

    @field_validator("longitude")
    def validate_longitude(cls, v):
        if not -180 <= v <= 180:
            raise ValueError("Longitude mora biti između -180 i 180")
        return v

class DriverResponse(BaseModel):
    id: int
    name: str
    status: str

    class Config:
        from_attributes = True

class LocationResponse(BaseModel):
    id: int
    driver_id: int
    latitude: float
    longitude: float
    timestamp: datetime

    class Config:
        from_attributes = True

class RideRequest(BaseModel):
    passenger_name: str
    pickup_lat: float
    pickup_lon: float

class RideResponse(BaseModel):
    id: int
    driver_id: int
    passenger_name: str
    status: str
    pickup_lat: float
    pickup_lon: float
    dropoff_lat: Optional[float]
    dropoff_lon: Optional[float]
    requested_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True