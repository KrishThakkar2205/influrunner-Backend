from sqlalchemy.orm import Session
from models import Influencer
from datetime import datetime, timedelta

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
    if influencer and influencer.signup_otp == str(otp) and influencer.updated_at < datetime.utcnow() - timedelta(minutes=10):
        influencer.signup_otp = None
        influencer.signup_status = "verified"
        db.commit()
        return True
    print(influencer.updated_at < datetime.utcnow() - timedelta(minutes=10))
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
