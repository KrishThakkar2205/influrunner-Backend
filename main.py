from accessToken import CreateAccessToken, VerifyAccessToken, get_current_user
from fastapi import FastAPI, Request, Response, Depends
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from database import get_db
from sqlalchemy.orm import Session
from databaseAccess import GetDashboard, AddSocialMedia, ValidateReviewToken, AddInfluencers, VerifyOTP, FinalSignup, Login, GetProfile, AddShoot, GetShoots, UpdateShoot, DeleteShoot,AddUpload, GetUploads, GetUpload,UpdateUploads, DeleteUpload, GenerateReview
from schema.auth import ReviewResponse,SignupInitiate, VerifyOtp, SignupFinal, LoginSchema, ShootCreate, ShootUpdate, UploadCreate, UploadResponse, UploadUpdate, ReviewSubmit
from maiService import send_otp_email
from accessToken import CreateAccessToken, VerifyAccessToken
from typing import Optional
from datetime import date, time, datetime, timedelta
import uvicorn
import random
import requests 

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # production me specific domain use karna
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/auth/signup-initiate")
async def signup_initiate(request: SignupInitiate, db: Session = Depends(get_db)):
    try:
        otp = random.randint(100000, 999999)
        if AddInfluencers(
            db,
            email_id=request.email_id,
            phone_number=request.phone_number,
            name=request.name,
            password=request.password,
            otp=otp
        ):
            send_otp_email(request.email_id, otp)
            return Response(status_code=200, content="OTP sent successfully")
        return Response(status_code=400, content="User already exists")
    except Exception as e:
        print(e)
        return Response(status_code=500, content=str(e))

@app.post("/auth/verify-otp")
async def verify_otp(request: VerifyOtp, db: Session = Depends(get_db)):
    try:
        if VerifyOTP(db, email_id=request.email_id, otp=request.otp):
            return Response(status_code=200, content="OTP verified successfully")
        return Response(status_code=400, content="Invalid OTP")
    except Exception as e:
        print(e)
        return Response(status_code=500, content=str(e))

@app.post("/auth/signup-final")
async def signup_final(request: SignupFinal, db: Session = Depends(get_db)):
    try:
        id = FinalSignup(
            db,
            email_id=request.email_id,
            min_price=request.min_price,
            max_price=request.max_price,
            categories=request.categories,
            location=request.location
        )
        if id:
            token = CreateAccessToken(id)
            return {"access_token":token, "type":"Bearer"}
        return Response(status_code=400, content="User not found")
    except Exception as e:
        print(e)
        return Response(status_code=500, content=str(e))

@app.post("/auth/login")
async def login(request: LoginSchema, db: Session = Depends(get_db)):
    try:
        id = Login(db, email_id=request.email_id, password=request.password)
        if id:
            token = CreateAccessToken(id)
            return {"access_token":token, "type":"Bearer"}
        return Response(status_code=400, content="Invalid credentials")
    except Exception as e:
        print(e)
        return Response(status_code=500, content=str(e))

@app.get("/api/profile")
async def get_profile(request: str = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get current user's profile"""
    token = request
    user_id = VerifyAccessToken(token)
    if user_id:
        return GetProfile(db, user_id)
    return Response(status_code=401, content="Invalid token")

@app.post("/api/shoots")
async def create_shoot(shoot: ShootCreate, token: str = Depends(get_current_user), db: Session = Depends(get_db)):
    """Create a new shoot"""
    user_id = VerifyAccessToken(token)
    if not user_id:
        return Response(status_code=401, content="Invalid token")
    
    
    return AddShoot(db, user_id, shoot.shoot_date, shoot.shoot_time, shoot.location, shoot.name, shoot.brand_name, shoot.notes)

@app.get("/api/shoots")
async def get_shoots(token: str = Depends(get_current_user),db: Session = Depends(get_db),completed: Optional[bool] = None,start_date: Optional[date] = None,end_date: Optional[date] = None):
    """Get all shoots for current user with optional filters"""
    user_id = VerifyAccessToken(token)
    if not user_id:
        return Response(status_code=401, content="Invalid token")
    return GetShoots(db, user_id, completed, start_date, end_date)

@app.put("/api/shoots/{shoot_id}")
async def update_shoot(shoot_id: str, shoot_update: ShootUpdate,token: str = Depends(get_current_user), db: Session = Depends(get_db)):
    """Update a shoot (including rescheduling)"""
    user_id = VerifyAccessToken(token)
    if not user_id:
        return Response(status_code=401, content="Invalid token")
    return UpdateShoot(db, user_id, shoot_id, shoot_update)

@app.delete("/api/shoots/{shoot_id}")
async def delete_shoot(shoot_id: str, db: Session = Depends(get_db), token: str = Depends(get_current_user)):
    """Soft delete a shoot"""
    user_id = VerifyAccessToken(token)
    if not user_id:
        return Response(status_code=401, content="Invalid token")
    DeleteShoot(db, user_id, shoot_id)
    return {"message": "Shoot deleted successfully", "status": "success"}

@app.get("/api/shoots/{shoot_id}")
async def get_shoot(shoot_id: str, db: Session = Depends(get_db), token: str = Depends(get_current_user)):
    """Get a specific shoot"""
    user_id = VerifyAccessToken(token)
    if not user_id:
        return Response(status_code=401, content="Invalid token")
    return GetShoot(db, user_id, shoot_id)

@app.post("/api/uploads")
async def create_upload(upload: UploadCreate, db: Session = Depends(get_db), token: str = Depends(get_current_user)):
    """Create a new upload"""
    user_id = VerifyAccessToken(token)
    if not user_id:
        return Response(status_code=401, content="Invalid token")
    return AddUpload(db, user_id, upload)

@app.get("/api/uploads", response_model=list[UploadResponse])
async def get_uploads(token: str = Depends(get_current_user),db: Session = Depends(get_db),completed: Optional[bool] = None,start_date: Optional[date] = None,end_date: Optional[date] = None,platform: Optional[str] = None):
    """Get all uploads for current user with optional filters"""
    user_id = VerifyAccessToken(token)
    if not user_id:
        return Response(status_code=401, content="Invalid token")
    
    return GetUploads(db, user_id, completed, start_date, end_date, platform)

@app.get("/api/uploads/{upload_id}", response_model=UploadResponse)
async def get_upload(upload_id: str, db: Session = Depends(get_db), token: str = Depends(get_current_user)):
    """Get a specific upload"""
    user_id = VerifyAccessToken(token)
    if not user_id:
        return Response(status_code=401, content="Invalid token")
    
    return GetUpload(db, user_id, upload_id)

@app.put("/api/uploads/{upload_id}", response_model=UploadResponse)
async def update_upload(upload_id: str, upload_update: UploadUpdate, db: Session = Depends(get_db), token: str = Depends(get_current_user)):
    """Update an upload (including rescheduling)"""
    user_id = VerifyAccessToken(token)
    if not user_id:
        return Response(status_code=401, content="Invalid token")
    return UpdateUploads(db, user_id, upload_id, upload_update)

@app.delete("/api/uploads/{upload_id}")
async def delete_upload(upload_id: str, db: Session = Depends(get_db), token: str = Depends(get_current_user)):
    """Soft delete an upload"""
    user_id = VerifyAccessToken(token)
    if not user_id:
        return Response(status_code=401, content="Invalid token")
    
    DeleteUpload(db, user_id, upload_id)
    
    return {"message": "Upload deleted successfully", "status": "success"}

@app.post("/api/reviews/generate/{shoot_id}")
async def generate_review_link(shoot_id: str, db: Session = Depends(get_db), token: str = Depends(get_current_user)):
    """Generate a unique review link for a completed shoot"""
    user_id = VerifyAccessToken(token)
    if not user_id:
        return Response(status_code=401, content="Invalid token")
    review_link = GenerateReview(db, user_id, shoot_id)
    return {"review_link": review_link}

@app.get("/api/reviews/validate/{token}")
async def validate_review_token(token: str, db: Session = Depends(get_db)):
    """Validate a review token and return shoot details"""
    return ValidateReviewToken(db, token)

@app.post("/api/reviews/submit/{token}")
async def submit_review(token: str, review_data: ReviewSubmit, db: Session = Depends(get_db)):
    """Submit a client review"""
    return SubmitReview(db, token, review_data)

@app.get("/api/reviews", response_model=list[ReviewResponse])
async def get_reviews(db: Session = Depends(get_db), token: str = Depends(get_current_user)):
    """Get all reviews for current user"""
    user_id = VerifyAccessToken(token)
    if not user_id:
        return Response(status_code=401, content="Invalid token")
    return GetReviews(db, user_id)

@app.get("/api/social-media/connect/{platform}")
async def connect_social_media(request: Request, platform: str, db: Session = Depends(get_db), token:str = Depends(get_current_user)):
    """Initiate OAuth connection for social media platform"""
    user_id = VerifyAccessToken(token)
    if not user_id:
        return Response(status_code=401, content="Invalid token")
    if platform not in ["instagram", "facebook", "youtube"]:
        raise HTTPException(status_code=400, detail="Invalid platform")
    if platform == "instagram":
        url = f"https://www.instagram.com/oauth/authorize?force_reauth=true&client_id=2447536092327866&redirect_uri=https://api.influrunner.com/redirect/instagram&response_type=code&state={user_id}&scope=instagram_business_basic%2Cinstagram_business_manage_messages%2Cinstagram_business_manage_comments%2Cinstagram_business_content_publish%2Cinstagram_business_manage_insights"
        return RedirectResponse(url)

@app.get("/redirect/instagram")
async def instagram_redirect(code: str, state: str, db: Session = Depends(get_db)):
    """Handle Instagram OAuth redirect"""
    try:
        influencer_id = state
        # Exchanging the Auth Code for the short lived access token
        url = "https://api.instagram.com/oauth/access_token"

        payload = {
            "client_id": "2447536092327866",
            "client_secret": "68d658c3f4e135f6f8e289f0af95def4",
            "grant_type": "authorization_code",
            "redirect_uri": "https://api.influrunner.com/redirect/instagram",
            "code": code
        }

        response = requests.post(url, data=payload)
        data = response.json()
        temp_access_token = data.get("access_token")
        platform_user_id = data.get("user_id")

        # Exchanging the short lived access token for the long live access token
        url = "https://graph.instagram.com/access_token"
        payload = {
            "client_secret": "68d658c3f4e135f6f8e289f0af95def4",
            "grant_type": "ig_exchange_token",
            "access_token" : temp_access_token,
        }
        response =  requests.get(url, params=payload)
        data = response.json()
        access_token = data.get("access_token")
        expires_in_seconds = data.get("expires_in")
        expires_in = datetime.utcnow() + timedelta(seconds=expires_in_seconds)
        
        AddSocialMedia(db, influencer_id, platform_user_id, access_token, access_token, expires_in, "instagram")

        return RedirectResponse("https://influrunner.com/?auth_status=success")
    except Exception as e:
        print(e)
        return RedirectResponse("https://influrunner.com/?auth_status=fail")

@app.get("/dashboard-card")
async def dashboard(db: Session = Depends(get_db), token: str = Depends(get_current_user)):
    """Get dashboard data"""
    user_id = VerifyAccessToken(token)
    if not user_id:
        return Response(status_code=401, content="Invalid token")
    return GetDashboard(db, user_id)

@app.get("/dashboard-shoot-upload")
async def dashboard_shoot_upload(db: Session = Depends(get_db), token: str = Depends(get_current_user)):
    """Get dashboard shoot upload data"""
    user_id = VerifyAccessToken(token)
    if not user_id:
        return Response(status_code=401, content="Invalid token")
    return GetDashboardShootUpload(db, user_id)
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000)