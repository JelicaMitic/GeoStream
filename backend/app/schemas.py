from pydantic import BaseModel, field_validator
from datetime import datetime

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