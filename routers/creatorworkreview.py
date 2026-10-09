from asyncio import timeout
from fastapi import APIRouter,Depends,Request,Response
from sqlalchemy.orm import Session
from database import get_db
from datetime import datetime, timedelta
from models import CreatorReviewsOnInfluRunner
import hashlib
import httpx

router = APIRouter(
    prefix="/creatorreview",
    tags=["Creator Review"]
)

@router.get("/validate/review/creator")
async def validate_review_link(req:Request,review_id: str, db:Session = Depends(get_db)):
    try:
        review = db.query(CreatorReviewsOnInfluRunner).filter(CreatorReviewsOnInfluRunner.id == review_id, CreatorReviewsOnInfluRunner.status == "pending").first()
        if review:
            return Response(status_code = 200, content="Review is valid")
        return Response(status_code=404, content="Review not found")
    except Exception as e:
        print(e)
        return Response(status_code=500, content=str(e))

@router.post("/submit/review/creator")
async def submit_review(req:Request, review_id: str, db:Session = Depends(get_db)):
    try:
        data = await req.json()
        review = db.query(CreatorReviewsOnInfluRunner).filter(CreatorReviewsOnInfluRunner.id == review_id).first()
        if review:
            review.rating = data.get("rating")
            review.review = data.get("review")
            review.positives = data.get("positives")
            review.negatives = data.get("negatives")
            review.status = "submitted"
            review.submitted = True
            review.submitted_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(review)
            return Response(status_code = 200, content="Review submitted successfully")
        return Response(status_code=404, content="Review not found")
    except Exception as e:
        print(e)
        return Response(status_code=500, content=str(e))

@router.get("/get/review/publised")
async def publised_reviews(req:Request,db:Session = Depends(get_db)):
    try:
        reviews = db.query(CreatorReviewsOnInfluRunner).filter(CreatorReviewsOnInfluRunner.status == "published").all()
        return Response(status_code=200, content=reviews)
    except Exception as e:
        print(e)
        return Response(status_code=500, content=str(e))