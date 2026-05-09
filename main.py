from asyncio import sleep
from accessToken import CreateAccessToken, VerifyAccessToken, get_current_user
from fastapi import FastAPI, Request, Response, Depends, UploadFile, File, Form
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from database import get_db
from sqlalchemy.orm import Session
from databaseAccess import DeleteCollabNotification, GetDashboardCollabNotification, CollabNotification, RegisterToken, GetInstaMetricPerMedia, GetInstaMediaPortfolioMetric, GetInstaPortfolioMetric, EditProfile, GetPortfolio, SubmitReview, GetReviews, GetDashboard, AddSocialMedia, ValidateReviewToken, AddInfluencers, VerifyOTP, FinalSignup, Login, GetProfile, AddShoot, GetShoots, UpdateShoot, DeleteShoot,AddUpload, GetUploads, GetUpload,UpdateUploads, DeleteUpload, GenerateReview
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
from backgound_workers.welcome import connect_instagram
import firebase.firebase_config
from backgound_workers.whatsapp_shoot_upload_reaminder import send_shoot_reminder_bfr_2hr, send_shoot_reminder_bfr_1hr


UPLOAD_DIR = "uploads/profile_pictures"

app = FastAPI()
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
    scheduler.add_job(connect_instagram, 'cron', hour=0, minute = 14, id = "connect_instagram")
    scheduler.add_job(send_shoot_reminder_bfr_2hr, 'interval', minutes=1, id = "send_shoot_reminder_bfr_2hr")
    scheduler.add_job(send_shoot_reminder_bfr_1hr, 'interval', minutes=1, id = "send_shoot_reminder_bfr_1hr")
    scheduler.start()

@app.on_event("shutdown")
def stop_scheduler():
    scheduler.shutdown()

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
        url = f"https://www.instagram.com/oauth/authorize?force_reauth=true&client_id=1780741403310636&redirect_uri=https://api.influrunner.com/redirect/instagram&response_type=code&state={user_id}&scope=instagram_business_basic%2Cinstagram_business_manage_insights"
        return {"url": url}

@app.get("/redirect/instagram")
async def instagram_redirect(code: str, state: str, db: Session = Depends(get_db)):
    """Handle Instagram OAuth redirect"""
    try:
        print("Code: ", code)
        print("State: ", state)
        influencer_id = state

        # ── Step 1: Exchange Auth Code → Short-Lived Token ──────────────────
        step1_url = "https://api.instagram.com/oauth/access_token"
        step1_payload = {
            "client_id": "1780741403310636",
            "client_secret": "fa13fbc50f5ffc6d3fbc3cdce088b045",
            "grant_type": "authorization_code",
            "redirect_uri": "https://api.influrunner.com/redirect/instagram",
            "code": code
        }
        step1_response = requests.post(step1_url, data=step1_payload)
        step1_data = step1_response.json()
        print("[Step 1] Status:", step1_response.status_code)
        print("[Step 1] Response:", step1_response.text)

        temp_access_token = step1_data.get("access_token")
        platform_user_id = step1_data.get("user_id")
        print("[Step 1] Temp Access Token:", temp_access_token)
        print("[Step 1] Platform User ID:", platform_user_id)

        if not temp_access_token:
            print("[Step 1] ERROR: Failed to get short-lived token. Full response:", step1_data)
            return RedirectResponse("https://influrunner.com/influencer?auth_status=fail")

        # ── Step 1.5: Debug Token — check actual expiry from Meta debugger ──────
        # Uses Facebook App ID|Secret as the app access token for introspection
        INSTAGRAM_APP_SECRET = "fa13fbc50f5ffc6d3fbc3cdce088b045"

        # ── Step 2: Verify token via API call (using Authorization header) ─────
        # The new Instagram Business Login API (graph.instagram.com) requires the
        # access token in the "Authorization: Bearer" header, NOT as ?access_token=
        # query param. The old style causes "Unsupported request - method type: get".
        auth_headers = {"Authorization": f"Bearer {temp_access_token}"}

        verify_response = requests.get(
            f"https://graph.instagram.com/{platform_user_id}",
            headers=auth_headers,
            params={"fields": "id,username"},
        )
        print("[Step 2 Verify] Status:", verify_response.status_code)
        print("[Step 2 Verify] Response:", verify_response.text)

        if verify_response.status_code != 200:
            print("[Step 2 Verify] ERROR: Token verification failed:", verify_response.text)
            return RedirectResponse("https://influrunner.com/influencer?auth_status=fail")

        verify_data = verify_response.json()
        print("[Step 2 Verify] Username:", verify_data.get("username"))
        print("[Step 2 Verify] Token is valid and working ✓")

        # ── Step 3: Try long-lived token exchange (using Authorization header) ──
        # Now that we know Bearer auth works, retry the exchange the correct way.
        exchange_response = requests.get(
            "https://graph.instagram.com/access_token",
            headers=auth_headers,
            params={
                "grant_type": "ig_exchange_token",
                "client_secret": INSTAGRAM_APP_SECRET,
            },
        )
        print("[Step 3 Exchange] Status:", exchange_response.status_code)
        print("[Step 3 Exchange] Response:", exchange_response.text)
        exchange_data = exchange_response.json()

        long_lived_token = exchange_data.get("access_token")
        expires_in_seconds = exchange_data.get("expires_in")

        if long_lived_token and expires_in_seconds:
            print(f"[Step 3 Exchange] ✓ Got long-lived token. Expires in {expires_in_seconds}s ({expires_in_seconds//86400} days).")
            access_token = long_lived_token
            expires_in = datetime.utcnow() + timedelta(seconds=int(expires_in_seconds))
        else:
            # Fallback: store short-lived token directly (60-day assumption for new Business Login API)
            print("[Step 3 Exchange] Exchange not supported — storing token directly with 60-day expiry.")
            access_token = temp_access_token
            expires_in = datetime.utcnow() + timedelta(days=60)

        print("[Final] Storing access token, expires:", expires_in)

        AddSocialMedia(db, influencer_id, platform_user_id, access_token, access_token, expires_in, "instagram")

        return RedirectResponse("https://influrunner.com/influencer?auth_status=success")
    except Exception as e:
        print("[Instagram OAuth] Exception:", e)
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
    if profile_picture:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        file_extension = profile_picture.filename.split(".")[-1]
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        profile_data["profile_picture_location"] = file_path 
        async with aiofiles.open(file_path, "wb") as out_file:
            content = await profile_picture.read()
            await out_file.write(content)
    print(profile_data)
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
async def get_insta_metric_per_media(influencer_id: str, media_id: str, db: Session = Depends(get_db)):
    """Get Instagram metric per media"""
    if not influencer_id or not media_id:
        return Response(status_code=400, content="Missing influencer_id or media_id")
    return GetInstaMetricPerMedia(db, influencer_id,media_id)

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