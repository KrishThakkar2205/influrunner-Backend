from sqlalchemy.orm import Session
from models import Influencer, Shoots
from datetime import datetime, timedelta
from datetime import date, time
from typing import Optional
from schema.auth import ShootUpdate

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
    # Convert JSON categories to list
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
        "created_at": user.created_at
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
    query = db.query(Shoots).filter(
        Shoots.influencer_id == user_id,
        Shoots.deleted == False
    )
    
    if completed is not None:
        query = query.filter(Shoots.completed == completed)
    
    if start_date:
        query = query.filter(Shoots.shoot_date >= start_date)
    
    if end_date:
        query = query.filter(Shoots.shoot_date <= end_date)
    
    shoots = query.order_by(Shoots.shoot_date.desc()).all()
    return shoots

def GetShoot(db: Session, user_id: int, shoot_id: int):
    shoot = db.query(Shoots).filter(
        Shoots.id == shoot_id,
        Shoots.influencer_id == user_id,
        Shoots.deleted == False
    ).first()
    
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