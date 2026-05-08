from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Driver(Base):
    __tablename__ = "drivers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    status = Column(String, default="inactive")  # active / inactive
    
    locations = relationship("LocationEvent", back_populates="driver")
    rides = relationship("Ride", back_populates="driver")


class LocationEvent(Base):
    __tablename__ = "location_events"

    id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    driver = relationship("Driver", back_populates="locations")

class Ride(Base):
    __tablename__ = "rides"

    id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=False)
    passenger_name = Column(String, nullable=False)
    status = Column(String, default="requested")  # requested / active / completed
    pickup_lat = Column(Float, nullable=False)
    pickup_lon = Column(Float, nullable=False)
    dropoff_lat = Column(Float, nullable=True)
    dropoff_lon = Column(Float, nullable=True)
    requested_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    driver = relationship("Driver", back_populates="rides")