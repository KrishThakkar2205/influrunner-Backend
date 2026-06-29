from asyncio import sleep
from accessToken import CreateAccessToken, VerifyAccessToken, get_current_user
from fastapi import FastAPI, Request, Response, Depends, UploadFile, File, Form
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from database import get_db
from sqlalchemy.orm import Session
from databaseAccess import DeleteCollabNotification, GetDashboardCollabNotification, CollabNotification, RegisterToken, GetInstaMetricPerMedia, GetInstaMediaPortfolioMetric, GetInstaPortfolioMetric, EditProfile, GetPortfolio, SubmitReview, GetReviews, GetDashboard, AddSocialMedia, ValidateReviewToken, AddInfluencers, VerifyOTP, FinalSignup, Login, GetProfile, AddShoot, GetShoots, GetShoot, UpdateShoot, DeleteShoot,AddUpload, GetUploads, GetUpload,UpdateUploads, DeleteUpload, GenerateReview, GetSitemapData
from schema.auth import ReviewResponse,SignupInitiate, VerifyOtp, SignupFinal, LoginSchema, ShootCreate, ShootUpdate, UploadCreate, UploadResponse, UploadUpdate, ReviewSubmit
from maiService import send_otp_email
from accessToken import CreateAccessToken, VerifyAccessToken
from typing import Optional, List
from datetime import date, time, datetime, timedelta
from fastapi.staticfiles import StaticFiles
import uvicorn
import random
import requests 
import uuid
import os
import aiofiles
from apscheduler.schedulers.background import BackgroundScheduler
from backgound_workers.update_creds import update_creds
from backgound_workers.welcome import connect_instagram, add_to_calender_remainder
import firebase.firebase_config
from backgound_workers.whatsapp_shoot_upload_reaminder import send_shoot_reminder_bfr_2hr, send_shoot_reminder_bfr_1hr, upload_remainder_before_2hr, upload_remainder_before_1hr
from routers.portfolio_views import router as portfolio_views_router

UPLOAD_DIR = "uploads/profile_pictures"

app = FastAPI()
app.include_router(portfolio_views_router)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # production me specific domain use karna
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


scheduler = BackgroundScheduler()
@app.on_event("startup")
def start_scheduler():
    scheduler.add_job(update_creds, 'cron', hour=0, minute = 0, id = "update_creds")
    scheduler.add_job(connect_instagram, 'cron', hour=10, minute = 00, id = "connect_instagram")
    scheduler.add_job(add_to_calender_remainder, "cron", hour = 20, minute = 00, id = "add_to_calender_remainder")
    scheduler.add_job(send_shoot_reminder_bfr_2hr, 'interval', minutes=1, id = "send_shoot_reminder_bfr_2hr")
    scheduler.add_job(send_shoot_reminder_bfr_1hr, 'interval', minutes=1, id = "send_shoot_reminder_bfr_1hr")
    scheduler.add_job(upload_remainder_before_2hr, 'interval', minutes=1, id = "upload_remainder_before_2hr")
    scheduler.add_job(upload_remainder_before_1hr, 'interval', minutes=1, id = "upload_remainder_before_1hr")
    scheduler.start()

@app.on_event("shutdown")
def stop_scheduler():
    scheduler.shutdown()



@app.get("/api/portfolio/sitemap-data")
async def get_sitemap_data(db: Session = Depends(get_db)):
    try:
        data = GetSitemapData(db)
        response = []
        for item in data:
            response.append({
                "id": item.id,
                "created_at": item.created_at
            })
        return response
    except Exception as e:
        print(e)
        return Response(status_code=500, content=str(e))

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
        user = FinalSignup(
            db,
            email_id=request.email_id,
            min_price=request.min_price,
            max_price=request.max_price,
            categories=request.categories,
            location=request.location
        )
        if user:
            token = CreateAccessToken(user["id"])
            return {"access_token":token, "type":"Bearer", "id":user["id"], "name":user["name"], "profile_photo_location":user["profile_photo_location"]}
        return Response(status_code=400, content="User not found")
    except Exception as e:
        print(e)
        return Response(status_code=500, content=str(e))

@app.post("/auth/login")
async def login(request: LoginSchema, db: Session = Depends(get_db)):
    try:
        user = Login(db, email_id=request.email_id, password=request.password)
        if user:
            token = CreateAccessToken(user["id"])
            return {"access_token":token, "type":"Bearer", "id":user["id"], "name":user["name"], "profile_photo_location":user["profile_photo_location"]}
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

@app.post("/api/reviews/generate")
async def generate_review_link(brand_name: str,db: Session = Depends(get_db), token: str = Depends(get_current_user)):
    """Generate a unique review link for a completed shoot"""
    user_id = VerifyAccessToken(token)
    if not user_id:
        return Response(status_code=401, content="Invalid token")
    review_link = GenerateReview(db, user_id,brand_name)
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
        url = f"https://www.instagram.com/oauth/authorize?force_reauth=true&client_id=1780741403310636&redirect_uri=https://api.influrunner.com/redirect/instagram&response_type=code&state={user_id}&scope=instagram_business_basic%2Cinstagram_business_manage_insights"
        return {"url": url}

@app.get("/redirect/instagram")
async def instagram_redirect(code: str, state: str, db: Session = Depends(get_db)):
    """Handle Instagram OAuth redirect"""
    try:
        # print("Code: ", code)
        # print("State: ", state)
        influencer_id = state
        # Exchanging the Auth Code for the short lived access token
        url = "https://api.instagram.com/oauth/access_token"

        payload = {
            "client_id": "1780741403310636",
            "client_secret": "fa13fbc50f5ffc6d3fbc3cdce088b045",
            "grant_type": "authorization_code",
            "redirect_uri": "https://api.influrunner.com/redirect/instagram",
            "code": code
        }

        response = requests.post(url, data=payload)
        data = response.json()
        temp_access_token = data.get("access_token")
        platform_user_id = data.get("user_id")
        permission = data.get("permissions")
        # print("Temp Access Token: ", temp_access_token)
        # print("Platform User ID: ", platform_user_id)
        # print("Permissions: ", permission)

        # Exchanging the short lived access token for the long live access token
        url = "https://graph.instagram.com/access_token"
        payload = {
            "client_secret": "fa13fbc50f5ffc6d3fbc3cdce088b045",
            "grant_type": "ig_exchange_token",
            "access_token" : temp_access_token,
        }
        response =  requests.get(url, params=payload)
        data = response.json()
        # print(response.status_code, response.text)
        access_token = data.get("access_token")
        expires_in_seconds = data.get("expires_in")
        # print("Long Live Access Token: ", access_token)
        # print("Expires In Seconds: ", expires_in_seconds)
        expires_in = datetime.utcnow() + timedelta(seconds=expires_in_seconds)
        
        AddSocialMedia(db, influencer_id, platform_user_id, access_token, access_token, expires_in, "instagram")

        return RedirectResponse("https://influrunner.com/influencer?auth_status=success")
    except Exception as e:
        print(e)
        return RedirectResponse("https://influrunner.com/influencer?auth_status=fail")

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

@app.get("/api/portfolio/{infleuncer_id}")
async def get_public_portfolio(infleuncer_id: str, db: Session = Depends(get_db)):
    """Get public portfolio by username/email"""
    # Try to find user by email or name
    return GetPortfolio(db,infleuncer_id)

@app.put("/api/profile")
async def update_profile(
    name: Optional[str] = Form(None),
    bio: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    min_price: Optional[float] = Form(None),
    max_price: Optional[float] = Form(None),
    categories: Optional[List[str]] = Form(None),  # JSON string
    profile_picture: Optional[UploadFile] = File(None),
    whatsapp_notification: Optional[bool] = Form(None),
    db: Session = Depends(get_db),
    token: str = Depends(get_current_user)
):
    """Update user profile"""

    user_id = VerifyAccessToken(token)
    if not user_id:
        return Response(status_code=401, content="Invalid token")
    
    profile_data = {}
    if name:
        profile_data["name"] = name
    if bio:
        profile_data["bio"] = bio
    if location:
        profile_data["location"] = location
    if min_price:
        profile_data["min_price"] = min_price
    if max_price:
        profile_data["max_price"] = max_price
    if categories:
        profile_data["categories"] = categories
    if whatsapp_notification is not None:
        profile_data["whatsapp_notification"] = whatsapp_notification
    if profile_picture:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        file_extension = profile_picture.filename.split(".")[-1]
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        profile_data["profile_picture_location"] = file_path 
        async with aiofiles.open(file_path, "wb") as out_file:
            content = await profile_picture.read()
            await out_file.write(content)
    # print(profile_data)
    await EditProfile(db, user_id, profile_data)
    return Response(status_code=200, content="Profile updated successfully")


@app.get("/api/insta-portfolio-metric")
async def get_insta_portfolio_metric(influencer_id: str, db: Session = Depends(get_db)):
    """Get Instagram portfolio metric"""
    return GetInstaPortfolioMetric(db, influencer_id)

@app.get("/api/insta-portfolio-media-metric")
async def get_insta_portfolio_media_metric(influencer_id: str, db: Session = Depends(get_db)):
    """Get Instagram portfolio media metric"""
    return GetInstaMediaPortfolioMetric(db, influencer_id)

@app.get("/api/insta-metric-per-media")
async def get_insta_metric_per_media(influencer_id: str, media_id: str, media_type:str , db: Session = Depends(get_db)):
    """Get Instagram metric per media"""
    if not influencer_id or not media_id or not media_type:
        return Response(status_code=400, content="Missing influencer_id or media_id or media_type")
    return GetInstaMetricPerMedia(db, influencer_id,media_id,media_type)

@app.get("/api/dashboard-insta-metric")
async def get_dashboard_insta_metric(db: Session = Depends(get_db), token: str = Depends(get_current_user)):
    """Get Dashboard Instagram metric"""
    user_id = VerifyAccessToken(token)
    if not user_id:
        return Response(status_code=401, content="Invalid token")
    return GetInstaPortfolioMetric(db, user_id)

@app.post("/api/notifications/register-token")
async def register_token(request: Request, db: Session = Depends(get_db), token: str = Depends(get_current_user)):
    """Register device token"""
    user_id = VerifyAccessToken(token)
    if not user_id:
        return Response(status_code=401, content="Invalid token")
    data = await request.json()
    device_token = data.get("token")
    device_type = data.get("platform")
    if RegisterToken(db, user_id, device_token, device_type):
        return Response(status_code=200, content="Token registered successfully")
    return Response(status_code=400, content="Token not registered")

@app.post("/api/collab-notification")
async def collab_notification(request: Request, db: Session = Depends(get_db)):
    """Register device token"""
    data = await request.json()
    influencer_id = data.get("influencer_id")
    brand_name = data.get("brand_name")
    person_name = data.get("contact_person_name")
    person_phone = data.get("person_phone_number")
    person_email = data.get("person_email")
    budget = data.get("budget")
    business_info = data.get("business_info")
    notes = data.get("notes")
    if CollabNotification(db, influencer_id, brand_name, person_name, person_phone, person_email, budget, business_info, notes):
        return JSONResponse(status_code=200, content={"message": "Collab notification sent successfully"})
    return JSONResponse(status_code=400, content={"message": "Collab notification not sent"})

@app.get("/api/dashboard-collab-notification")
async def get_dashboard_collab_notification(db: Session = Depends(get_db), token: str = Depends(get_current_user)):
    """Get Dashboard Collab notification"""
    user_id = VerifyAccessToken(token)
    if not user_id:
        return Response(status_code=401, content="Invalid token")
    return GetDashboardCollabNotification(db, user_id)

@app.delete("/api/collab-notification/{notification_id}")
async def delete_collab_notification(notification_id: str, db: Session = Depends(get_db), token: str = Depends(get_current_user)):
    """Delete collab notification"""
    user_id = VerifyAccessToken(token)
    if not user_id:
        return Response(status_code=401, content="Invalid token")
    if DeleteCollabNotification(db, notification_id):
        return Response(status_code=200, content="Collab notification deleted successfully")
    return Response(status_code=400, content="Collab notification not deleted")

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000)