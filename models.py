from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Date, Time, Boolean
from sqlalchemy.dialects.postgresql import ARRAY
from database import Base
from datetime import datetime
import uuid

class Influencer(Base):
    __tablename__ = "influencers"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String,nullable=False)
    email_id = Column(String, unique=True, nullable=False)
    phone_number = Column(String, unique=True, nullable=False)
    categories = Column(ARRAY(String), nullable=True)
    location = Column(String, nullable=True)
    min_price = Column(Integer, nullable=True)
    max_price = Column(Integer, nullable=True)
    signup_status = Column(String, default="pending")
    signup_otp = Column(String, nullable=True)
    profile_picture_location = Column(String, nullable=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate= datetime.utcnow)
    deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    bio = Column(String, nullable=True)

class Uploads(Base):
    __tablename__ = "uploads"

    id = Column(String, primary_key=True, index=True,default=lambda: str(uuid.uuid4()))
    influencer_id = Column(String, ForeignKey("influencers.id"), nullable=False)
    upload_date = Column(Date, default=lambda: datetime.utcnow().date())
    upload_time = Column(Time, default=lambda:datetime.utcnow().time())
    name = Column(String, nullable=True)
    platform = Column(String, nullable=True)
    brand_name = Column(String, nullable=True)
    completed = Column(Boolean, nullable=False, default=False)
    completed_at = Column(DateTime, nullable=True)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)

class Shoots(Base):
    __tablename__ = "shoots"

    id = Column(String, primary_key=True,index=True,default=lambda: str(uuid.uuid4()))
    influencer_id = Column(String, ForeignKey("influencers.id"), nullable=False)
    shoot_date = Column(Date, nullable=True)
    shoot_time = Column(Time, nullable=True)
    location = Column(String, nullable=True)
    name = Column(String, nullable=True)
    brand_name = Column(String, nullable=True)
    completed = Column(Boolean, nullable=False, default=False)
    completed_at = Column(DateTime, nullable=True)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)

class Credentials(Base):
    __tablename__ = "credentials"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    influencer_id = Column(String, ForeignKey("influencers.id"), nullable=False)
    platform = Column(String, nullable=False)
    username = Column(String, nullable=False)
    access_token = Column(String, nullable=False)
    refresh_token = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    refreshed_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

class Reviews(Base):
    __tablename__ = "reviews"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    influencer_id = Column(String, ForeignKey("influencers.id"), nullable=False)
    shoot_id = Column(String, ForeignKey("shoots.id"), nullable=True)
    upload_id = Column(String, ForeignKey("uploads.id"), nullable=True)
    reviewer_name = Column(String, nullable=False)
    reviewer_phone = Column(String, nullable=False)
    reviewer_email = Column(String, nullable=False)
    rating = Column(Integer, nullable=False)
    review = Column(String, nullable=True)
    submitted = Column(Boolean, default=False)
    submitted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)