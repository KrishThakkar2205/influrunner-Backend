from asyncio import timeout
from fastapi import APIRouter,Depends,Request,Response
from sqlalchemy.orm import Session
from database import get_db
from datetime import datetime, timedelta
from models import CreatorReviewsOnInfluRunner, Admins
from accessToken import get_admin_credentials, VerifyAdminAccessToken, CreateAdminAccessToken
import bcrypt

router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)

@router.post("/generate",tags=["Creator Review"])
async def portfolio_view(req:Request,creator_name: str, db:Session = Depends(get_db)):
    try:
        review = CreatorReviewsOnInfluRunner(
            creator_name=creator_name
        )
        db.add(review)
        db.commit()
        db.refresh(review)
        review_id = review.id
        review_link = f"/creatorreview/{review_id}"
        return {"review_link":review_link, "status_code":200}
    except Exception as e:
        print(e)
        return {"status_code":500, "error":str(e)}

@router.get("/get/all/reviews")
async def get_all_reviews(req:Request, db:Session = Depends(get_db), token: str = Depends(get_admin_credentials)):
    try:
        result = VerifyAdminAccessToken(token)
        if not result:
            return Response(status_code=401, content="Invalid Admin Token")
        admin_id, role = result
        reviews = db.query(CreatorReviewsOnInfluRunner).all()
        return Response(status_code=200, content=reviews)
    except Exception as e:
        print(e)
        return Response(status_code=500, content=str(e))

@router.post("/changestatus/review/creator")
async def change_status(req:Request, db:Session = Depends(get_db),token: str = Depends(get_admin_credentials)):
    try:
        result = VerifyAdminAccessToken(token)
        if not result:
            return Response(status_code=401, content="Invalid Admin Token")
        admin_id, role = result
        data = await req.json()
        review_id = data.get("review_id")
        status = data.get("status")
        review = db.query(CreatorReviewsOnInfluRunner).filter(CreatorReviewsOnInfluRunner.id == review_id).first()
        if review:
            review.status = status
            db.commit()
            db.refresh(review)
            return Response(status_code = 200, content="Review status changed successfully")
        return Response(status_code=404, content="Review not found")
    except Exception as e:
        print(e)
        return Response(status_code=500, content=str(e))

@router.post("/login")
async def login(req:Request, db:Session = Depends(get_db)):
    try:
        data =  await req.json()
        email_id = data.get("email_id")
        password = data.get("password")
        admin = db.query(Admins).filter(Admins.email_id == email_id).first()
        if admin and bcrypt.checkpw(password.encode('utf-8'), admin.password_hash.encode('utf-8')):
            token = CreateAdminAccessToken(admin.id, admin.role)
            return {"access_token":token, "type":"Bearer"}
        return Response(status_code=401, content="Invalid Admin Credentials")
    except Exception as e:
        print(e)
        return Response(status_code=500, content=str(e))
        