from accessToken import CreateAccessToken
from fastapi import FastAPI, Request, Response, Depends
from database import get_db
from sqlalchemy.orm import Session
from databaseAccess import AddInfluencers, VerifyOTP, FinalSignup, Login
from schema.auth import SignupInitiate, VerifyOtp, SignupFinal, LoginSchema
from maiService import send_otp_email
from accessToken import CreateAccessToken
import uvicorn
import random

app = FastAPI()

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

@app.get("/dashboard")
async def dashboard(request: Request, db: Session = Depends(get_db)):
    try:
        token = request.headers.get("Authorization")
        if token:
            profile_id = VerifyAccessToken(token)
            if profile_id:
                return Response(status_code=200, content="Dashboard")
            return Response(status_code=401, content="Invalid token")
        return Response(status_code=401, content="Token not found")
    except Exception as e:
        print(e)
        return Response(status_code=500, content=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8080, reload=True)