import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from .database import Base # Import Base from our database connection

class User(Base):
    __tablename__ = "users"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to Bookings
    bookings = relationship("Booking", back_populates="user")

class Driver(Base):
    __tablename__ = "drivers"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    wallet_balance = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)

    # Relationship to Bookings
    bookings = relationship("Booking", back_populates="driver")

class Booking(Base):
    __tablename__ = "bookings"
    booking_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    driver_id = Column(PG_UUID(as_uuid=True), ForeignKey("drivers.id"), nullable=True) # Nullable until matched
    total_fare = Column(Float, nullable=False)
    status = Column(String, default="PENDING", index=True) # e.g., 'PENDING', 'CONFIRMED', 'COMPLETED', 'CANCELLED'
    pickup_address = Column(String, nullable=False)
    drop_address = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships to User and Driver
    user = relationship("User", back_populates="bookings")
    driver = relationship("Driver", back_populates="bookings")