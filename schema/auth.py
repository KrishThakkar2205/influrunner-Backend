from pydantic import BaseModel, EmailStr, Field
from datetime import date, time, datetime
from typing import List, Optional


class SignupInitiate(BaseModel):
    email_id: EmailStr = Field(..., description="Email ID of the influencer")
    phone_number: str = Field(..., description="Phone number of the influencer")
    name: str = Field(..., description="Name of the influencer")
    password: str = Field(..., description="Password of the influencer")

class VerifyOtp(BaseModel):
    email_id: EmailStr = Field(..., description="Email ID of the influencer")
    otp: int = Field(..., description="OTP sent to the influencer")

class SignupFinal(BaseModel):
    email_id: EmailStr = Field(..., description="Email ID of the influencer")
    min_price: int = Field(..., description="Min Price of the influencer")
    max_price: int = Field(..., description="Max Price of the influencer")
    categories: list[str] = Field(..., description="Categories of the influencer")
    location: str = Field(..., description="Location of the influencer")

class LoginSchema(BaseModel):
    email_id: EmailStr = Field(..., description="Email ID of the influencer")
    password: str = Field(..., description="Password of the influencer")

class ShootCreate(BaseModel):
    shoot_date: date
    shoot_time: Optional[time] = None
    location: Optional[str] = None
    name: Optional[str] = None
    brand_name: Optional[str] = None
    notes: Optional[str] = None

class ShootUpdate(BaseModel):
    shoot_date: Optional[date] = None
    shoot_time: Optional[time] = None
    location: Optional[str] = None
    name: Optional[str] = None
    brand_name: Optional[str] = None
    notes: Optional[str] = None
    completed: Optional[bool] = None

class UploadCreate(BaseModel):
    upload_date: date
    upload_time: Optional[time] = None
    name: Optional[str] = None
    platform: Optional[str] = None
    brand_name: Optional[str] = None
    notes: Optional[str] = None

class UploadUpdate(BaseModel):
    upload_date: Optional[date] = None
    upload_time: Optional[time] = None
    name: Optional[str] = None
    platform: Optional[str] = None
    brand_name: Optional[str] = None
    notes: Optional[str] = None
    completed: Optional[bool] = None

class UploadResponse(BaseModel):
    id: str
    influencer_id: str
    upload_date: Optional[date]
    upload_time: Optional[time]
    name: Optional[str]
    platform: Optional[str]
    brand_name: Optional[str]
    completed: bool
    completed_at: Optional[datetime]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ReviewSubmit(BaseModel):
    reviewer_name: str
    reviewer_phone: str
    reviewer_email: EmailStr
    rating: int = Field(..., ge=1, le=5)
    review: Optional[str] = None

class ReviewResponse(BaseModel):
    id: str
    influencer_id: str
    shoot_id: Optional[str]
    reviewer_name: str
    reviewer_phone: str
    reviewer_email: str
    rating: int
    review: Optional[str]
    submitted: bool
    submitted_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True