from sqlalchemy.orm import Session
from sqlalchemy import func, case
from models import Influencer, Shoots, Uploads, Reviews, Credentials
from datetime import datetime, timedelta
from datetime import date, time
from fastapi import HTTPException
import requests
from typing import Optional
from schema.auth import ShootUpdate, UploadCreate, UploadUpdate, ReviewSubmit

def AddInfluencers(db: Session, name: str, email_id: str, phone_number: str, password: str, otp: int):
    influencer = db.query(Influencer).filter(Influencer.email_id == email_id).first()
    if influencer and influencer.signup_status == "completed":
        return False
    elif influencer and (influencer.signup_status == "verified"  or influencer.signup_status == "pending"):
        influencer.signup_otp = str(otp)
        influencer.signup_status = "pending"
        db.commit()
        return True
    else:
        influencer = Influencer(
            name=name,
            email_id=email_id,
            phone_number=phone_number,
            password_hash=password,
            signup_otp=str(otp),
        )
        db.add(influencer)
        db.commit()
        return True

def VerifyOTP(db: Session, email_id: str, otp: int):
    influencer = db.query(Influencer).filter(Influencer.email_id == email_id).first()
    if influencer and influencer.signup_otp == str(otp) and influencer.updated_at > datetime.utcnow() - timedelta(minutes=10):
        influencer.signup_otp = None
        influencer.signup_status = "verified"
        db.commit()
        return True
    print(influencer.updated_at > datetime.utcnow() - timedelta(minutes=10))
    print(influencer.signup_otp)
    return False

def FinalSignup(db: Session, email_id: str, min_price: int, max_price: int, categories: list[str], location: str):
    influencer = db.query(Influencer).filter(Influencer.email_id == email_id).first()
    id = influencer.id
    if influencer and influencer.signup_status == "verified":
        influencer.min_price = min_price
        influencer.max_price = max_price
        influencer.categories = categories
        influencer.signup_status = "completed"
        influencer.location = location
        db.commit()
        return id
    return None

def Login(db: Session, email_id: str, password: str):
    influencer = db.query(Influencer).filter(Influencer.email_id == email_id).first()
    if influencer and influencer.password_hash == password:
        return influencer.id
    return None

def GetProfile(db: Session, user_id: int):
    user = db.query(Influencer).filter(Influencer.id == user_id).first()
    if not user:
        return Response(status_code=404, content="User not found")
    platform = db.query(Credentials).filter(Credentials.influencer_id == user_id, Credentials.platform == "instagram").all()
    # Convert JSON categories to list
    if platform:
        user_dict = {
            "id": user.id,
            "name": user.name,
            "email_id": user.email_id,
            "phone_number": user.phone_number,
            "categories": user.categories,
            "location": user.location,
            "min_price": user.min_price,
            "max_price": user.max_price,
            "profile_picture_location": user.profile_picture_location,
            "created_at": user.created_at,
            "instagram": True,
            "bio":user.bio
        }
    else:
        user_dict = {
            "id": user.id,
            "name": user.name,
            "email_id": user.email_id,
            "phone_number": user.phone_number,
            "categories": user.categories,
            "location": user.location,
            "min_price": user.min_price,
            "max_price": user.max_price,
            "profile_picture_location": user.profile_picture_location,
            "created_at": user.created_at,
            "instagram": False,
            "bio":user.bio
        }
    
    return user_dict

def AddShoot(db: Session, user_id: int, shoot_date: date, shoot_time: time, location: str, name: str, brand_name: str, notes: str):
    new_shoot = Shoots(
        influencer_id=user_id,
        shoot_date=shoot_date,
        shoot_time=shoot_time,
        location=location,
        name=name,
        brand_name=brand_name,
        notes=notes
    )
    db.add(new_shoot)
    db.commit()
    db.refresh(new_shoot)
    return new_shoot

def GetShoots(db: Session, user_id: int, completed: Optional[bool] = None, start_date: Optional[date] = None, end_date: Optional[date] = None):
    results = db.query(
        Shoots,
        Reviews.id.label("review_id")
    ).outerjoin(
        Reviews, Reviews.shoot_id == Shoots.id
    ).filter(
        Shoots.influencer_id == user_id,
        Shoots.deleted == False
    )
    
    if completed is not None:
        results = results.filter(Shoots.completed == completed)
    
    if start_date:
        results = results.filter(Shoots.shoot_date >= start_date)
    
    if end_date:
        results = results.filter(Shoots.shoot_date <= end_date)
    results = results.order_by(Shoots.shoot_date.desc()).all()
    response = []
    for shoot, review_id in results:
        
        response.append({
        "shoot_date": shoot.shoot_date,
        "location": shoot.location,
        "brand_name": shoot.brand_name,
        "completed_at": shoot.completed_at,
        "created_at": shoot.created_at,
        "review_generated": shoot.review_generated,
        "shoot_time": shoot.shoot_time,
        "id": shoot.id,
        "influencer_id": shoot.influencer_id,
        "name": shoot.name,
        "completed": shoot.completed,
        "notes": shoot.notes,
        "updated_at": shoot.updated_at,
        "deleted_at": shoot.deleted_at,
        "review_id": review_id
    })
    # shoots = query.order_by(Shoots.shoot_date.desc()).all()
    # print(type(shoots[0]))
    return response

def GetShoot(db: Session, user_id: int, shoot_id: int):
    shoot = db.query(Shoots).filter(
        Shoots.id == shoot_id,
        Shoots.influencer_id == user_id,
        Shoots.deleted == False
    ).first()
    print(type(shoot))
    if not shoot:
        raise HTTPException(status_code=404, detail="Shoot not found")
    
    return shoot

def UpdateShoot(db: Session, user_id: int, shoot_id: int, shoot_update: ShootUpdate):
    shoot = db.query(Shoots).filter(
        Shoots.id == shoot_id,
        Shoots.influencer_id == user_id,
        Shoots.deleted == False
    ).first()
    
    if not shoot:
        raise HTTPException(status_code=404, detail="Shoot not found")
    
    # Update fields
    update_data = shoot_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(shoot, field, value)
    
    # If marking as completed, set completed_at
    if shoot_update.completed and not shoot.completed_at:
        shoot.completed_at = datetime.utcnow()
    
    shoot.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(shoot)
    
    return shoot

def DeleteShoot(db: Session, user_id: int, shoot_id: int):
    shoot = db.query(Shoots).filter(
        Shoots.id == shoot_id,
        Shoots.influencer_id == user_id,
        Shoots.deleted == False
    ).first()
    
    if not shoot:
        raise HTTPException(status_code=404, detail="Shoot not found")
    
    shoot.deleted = True
    shoot.deleted_at = datetime.utcnow()
    db.commit()
    db.refresh(shoot)
    
    return shoot

def AddUpload(db: Session, user_id: int, upload: UploadCreate):
    new_upload = Uploads(
        influencer_id=user_id,
        upload_date=upload.upload_date,
        upload_time=upload.upload_time,
        name=upload.name,
        platform=upload.platform,
        brand_name=upload.brand_name,
        notes=upload.notes
    )
    
    db.add(new_upload)
    db.commit()
    db.refresh(new_upload)
    
    return new_upload

def GetUploads(db: Session, user_id: int, completed: Optional[bool] = None, start_date: Optional[date] = None, end_date: Optional[date] = None, platform: Optional[str] = None):
    query = db.query(Uploads).filter(
        Uploads.influencer_id == user_id,
        Uploads.deleted == False
    )
    
    if completed is not None:
        query = query.filter(Uploads.completed == completed)
    
    if start_date:
        query = query.filter(Uploads.upload_date >= start_date)
    
    if end_date:
        query = query.filter(Uploads.upload_date <= end_date)
    
    if platform:
        query = query.filter(Uploads.platform == platform)
    
    uploads = query.order_by(Uploads.upload_date.desc()).all()
    return uploads

def GetUpload(db: Session, user_id: int, upload_id: int):
    upload = db.query(Uploads).filter(
        Uploads.id == upload_id,
        Uploads.influencer_id == user_id,
        Uploads.deleted == False
    ).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    return upload

def UpdateUploads(db: Session, user_id: int, upload_id: int, upload_update: UploadUpdate):
    upload = db.query(Uploads).filter(
        Uploads.id == upload_id,
        Uploads.influencer_id == user_id,
        Uploads.deleted == False
    ).first()
    
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    
    # Update fields
    update_data = upload_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(upload, field, value)
    
    # If marking as completed, set completed_at
    if upload_update.completed and not upload.completed_at:
        upload.completed_at = datetime.utcnow()
    
    upload.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(upload)
    
    return upload

def DeleteUpload(db: Session, user_id: int, upload_id: int):
    upload = db.query(Uploads).filter(
        Uploads.id == upload_id,
        Uploads.influencer_id == user_id,
        Uploads.deleted == False
    ).first()
    
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    
    upload.deleted = True
    upload.deleted_at = datetime.utcnow()
    db.commit()
    db.refresh(upload)
    
    return upload

def GenerateReview(db: Session, user_id: int, shoot_id: int):
    shoot = db.query(Shoots).filter(
        Shoots.id == shoot_id,
        Shoots.influencer_id == user_id,
        Shoots.deleted == False
    ).first()
    
    if not shoot:
        raise HTTPException(status_code=404, detail="Shoot not found")
    
    if not shoot.completed:
        raise HTTPException(status_code=400, detail="Shoot must be completed before generating review link")
    
    # Generate unique token
    # token = f"rev_{secrets.token_urlsafe(32)}"
    
    # Create review entry
    review = Reviews(
        influencer_id=user_id,
        shoot_id=shoot_id,
        reviewer_name="",  # Will be filled when client submits
        reviewer_phone="",
        reviewer_email="",
        rating=0,
        submitted=False
    )
    shoot.review_generated = True
    db.add(review)
    db.commit()
    db.refresh(review)
    db.refresh(shoot)
    
    # Update review ID to use as token (or store token separately)
    review_link = f"/review/{review.id}"
    return review_link

def ValidateReviewToken(db: Session, token: str):

    review = db.query(Reviews).filter(
        Reviews.id == token,
        Reviews.deleted == False
    ).first()
    
    if not review:
        raise HTTPException(status_code=404, detail="Invalid review link")
    
    if review.submitted:
        raise HTTPException(status_code=400, detail="Review already submitted")
    
    # Get shoot and influencer details
    shoot = db.query(Shoots.name, Shoots.brand_name, Shoots.shoot_date).filter(Shoots.id == review.shoot_id).first()
    influencer = db.query(Influencer.name).filter(Influencer.id == review.influencer_id).first()
    
    return {
        "influencer_name": influencer.name,
        "shoot_name": shoot.name if shoot.name else "Project",
        "brand_name": shoot.brand_name,
        "shoot_date": shoot.shoot_date
    }

def SubmitReview(db: Session, token: str, review_data: ReviewSubmit):
    review = db.query(Reviews).filter(
        Reviews.id == token,
        Reviews.deleted == False
    ).first()
    
    if not review:
        raise HTTPException(status_code=404, detail="Invalid review link")
    
    if review.submitted:
        raise HTTPException(status_code=400, detail="Review already submitted")
    
    # Update review with client data
    review.reviewer_name = review_data.reviewer_name
    review.reviewer_phone = review_data.reviewer_phone
    review.reviewer_email = review_data.reviewer_email
    review.rating = review_data.rating
    review.review = review_data.review
    review.submitted = True
    review.submitted_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Review submitted successfully", "status": "success"}

def GetReviews(db: Session, user_id: str):
    reviews = db.query(Reviews).filter(
        Reviews.influencer_id == user_id,
        Reviews.submitted == True,
        Reviews.deleted == False
    ).order_by(Reviews.submitted_at.desc()).all()
    
    return reviews

def AddSocialMedia(db: Session, influencer_id: str, platform_user_id: int,refresh_token: str , access_token: str, expires_in: datetime, platform: str):
    social_media = Credentials(
        influencer_id=influencer_id,
        username=platform_user_id,
        refresh_token=refresh_token,
        access_token=access_token,
        expires_at=expires_in,
        platform=platform
    )
    value = db.add(social_media)
    db.commit()
    db.refresh(social_media)
    print("Creds Added")

def GetDashboard(db: Session, user_id:str):
    today = datetime.utcnow()  # or datetime.now() if using local time
    first_day = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    # infleuncer = db.query(Influencer.name).filter(Influencer.id == user_id, Influencer.deleted == False)
    influencer_shoot_month = db.query(
        func.count(Shoots.id).label("total_shoots"),
        func.count(
            case(
                (Shoots.completed == True,1)
            )
        ).label("completed_shoots")
    ).filter(
        Shoots.influencer_id == user_id,
        Shoots.deleted == False,
        Shoots.created_at.between(first_day, today)
    ).first()
    average_rate = db.query(
        func.avg(Reviews.rating).label("average_rating")
    ).filter(
        Reviews.submitted == True,
        Reviews.deleted == False
    ).first()
    return {
        "total_shoot_this_month": influencer_shoot_month.total_shoots,
        "completed_shoots_this_month": influencer_shoot_month.completed_shoots,
        "average_rating": average_rate.average_rating or 0
    }

def GetPortfolio(db: Session, infleuncer_id: str):
    user = db.query(Influencer).filter(
        Influencer.id == infleuncer_id,
        Influencer.deleted == False,
        Influencer.signup_status == "completed"
    ).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    # Get reviews for this influencer
    reviews = db.query(Reviews).filter(
        Reviews.influencer_id == user.id,
        Reviews.submitted == True,
        Reviews.deleted == False
    ).order_by(Reviews.submitted_at.desc()).limit(10).all()
    
    average_rate = db.query(
        func.avg(Reviews.rating).label("average_rating")
    ).filter(
        Reviews.submitted == True,
        Reviews.deleted == False
    ).first()
    # Calculate average rating

    
    return {
        "name": user.name,
        "categories": user.categories,
        "location": user.location,
        "min_price": user.min_price,
        "max_price": user.max_price,
        "profile_picture": user.profile_picture_location,
        "avg_rating": average_rate.average_rating or 0,
        "total_reviews": len(reviews),
        "bio":user.bio,
        
        "reviews": [
            {
                "reviewer_name": r.reviewer_name,
                "rating": r.rating,
                "review": r.review,
                "submitted_at": r.submitted_at
            }
            for r in reviews[:5]  # Show only top 5 reviews
        ]
    }

async def EditProfile(db: Session, user_id: str, profile_data: dict):
    user = db.query(Influencer).filter(Influencer.id == user_id).first()
    
    # Update allowed fields
    allowed_fields = ['name', 'bio', 'location', 'min_price', 'max_price', 'profile_picture_location']
    for field in allowed_fields:
        if field in profile_data:
            setattr(user, field, profile_data[field])
    
    # Handle categories separately (JSON serialization)
    if 'categories' in profile_data:
        user.categories = profile_data['categories']
    
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)

def GetInstaMediaPortfolioMetric(db:Session, influencer_id: str):
    response_to_browser = {}
    credentials = db.query(Credentials.access_token, Credentials.refresh_token, Credentials.username).filter(
        Credentials.influencer_id == influencer_id,
        Credentials.platform == "instagram"
    ).first()
    if not credentials:
        raise HTTPException(status_code=404, detail="Credentials not found")
    #Media ID of the Account
    url = f"https://graph.instagram.com/v25.0/me/media?fields=id,media_url,thumbnail_url,media_type,caption,permalink,timestamp&limit=15&access_token={credentials.access_token}"
    response = requests.get(url)
    data = response.json()
    response_to_browser = data["data"]
    return response_to_browser

def GetInstaPortfolioMetric(db: Session, infleuncer_id: str):
    response_to_browser = {}
    credentials = db.query(Credentials.access_token, Credentials.refresh_token).filter(
        Credentials.influencer_id == infleuncer_id,
        Credentials.platform == "instagram"
    ).first()
    if not credentials:
        raise HTTPException(status_code=404, detail="Credentials not found")
    # Account Details
    url = f"https://graph.instagram.com/v25.0/me?fields=username,media_count,followers_count&access_token={credentials.access_token}"
    response = requests.get(url)
    data = response.json()
    response_to_browser["username"] = data["username"]
    response_to_browser["media_count"] = data["media_count"]
    response_to_browser["followers_count"] = data["followers_count"]
    # print(response_to_browser)
    #Account Metrices
    metrices = "accounts_engaged,reach,total_interactions,views"
    # 30 days from now
    since = int((datetime.utcnow() - timedelta(days=30)).timestamp())
    until = int((datetime.utcnow().timestamp()))
    url = f"https://graph.instagram.com/v25.0/{data['id']}/insights?metric={metrices}&period=day&since={since}&until={until}&metric_type=total_value&access_token={credentials.access_token}"
    response = requests.get(url)
    data = response.json()
    for item in data['data']:
        response_to_browser[item['name']] = item['total_value']['value']
    return response_to_browser

def GetInstaMetricPerMedia(db: Session, influencer_id: str, media_id: str):
    response_to_browser = {}
    credentials = db.query(Credentials.access_token, Credentials.refresh_token).filter(
        Credentials.influencer_id == influencer_id,
        Credentials.platform == "instagram"
    ).first()
    if not credentials:
        raise HTTPException(status_code=404, detail="Credentials not found")
    #Media ID of the Account
    url = f"https://graph.instagram.com/v25.0/{media_id}/insights?metric=accounts_engaged,reach,total_interactions,views&period=day&access_token={credentials.access_token}"