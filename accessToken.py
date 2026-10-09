from datetime import datetime, timedelta
from jose import jwt, JWTError
from dotenv import load_dotenv
import os
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends

load_dotenv()

SECRET_KEY = os.getenv("SECRET_TOKEN")
ALGORITHM = os.getenv("ALOGRITHM")
ADMIN_SECRET_KEY = os.getenv("ADMIN_SECRET_TOKEN")

def CreateAccessToken(profile_id):
    to_encode = {"profile_id": profile_id}
    expire = datetime.now() + timedelta(minutes=int(43200))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def CreateAdminAccessToken(admin_id, role):
    to_encode = {"admin_id": admin_id, "role": role}
    expire = datetime.now() + timedelta(minutes=int(43200))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, ADMIN_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_admin_credentials(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
):
    token = credentials.credentials
    return token

def VerifyAdminAccessToken(token):
    try:
        payload = jwt.decode(token, ADMIN_SECRET_KEY, algorithms=[ALGORITHM])
        admin_id: str = payload.get("admin_id")
        role: str = payload.get("role")
        if admin_id is None or role is None:
            return None
        return admin_id, role
    except JWTError:
        return None

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
):
    token = credentials.credentials
    return token

def VerifyAccessToken(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        profile_id: str = payload.get("profile_id")
        if profile_id is None:
            return None
        return profile_id
    except JWTError:
        return None
