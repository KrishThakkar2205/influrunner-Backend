from pydantic import BaseModel, EmailStr, Field

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
