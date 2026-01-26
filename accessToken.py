from datetime import datetime, timedelta
from jose import jwt, JWTError
from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = os.getenv("SECRET_TOKEN")
ALGORITHM = os.getenv("ALOGRITHM")

def CreateAccessToken(profile_id):
    to_encode = {"profile_id": profile_id}
    expire = datetime.now() + timedelta(minutes=int(43200))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def VerifyAccessToken(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        profile_id: str = payload.get("profile_id")
        if profile_id is None:
            return None
        return profile_id
    except JWTError:
        return None
