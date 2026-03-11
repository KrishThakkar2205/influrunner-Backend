from datetime import datetime, timedelta
from database import SessionLocal
from models import Credentials
import requests

def update_creds():
    db = SessionLocal()
    try:
        today = datetime.utcnow().date()
        five_days_later = today + timedelta(days=5)
        expired_creds = db.query(Credentials).filter(Credentials.expires_at.between(today, five_days_later)).all()
        if expired_creds:
            print(f"Found {len(expired_creds)} expired credentials")
            for cred in expired_creds:
                refresh_token = cred.refresh_token
                platform = cred.platform
                if platform == "instagram":
                    url = f"https://graph.instagram.com/refresh_access_token?grant_type=ig_refresh_token&access_token={refresh_token}"
                    response = requests.get(url)
                    if response.status_code == 200:
                        data = response.json()
                        cred.access_token = data["access_token"]
                        cred.expires_at = datetime.utcnow() + timedelta(days=60)
                        db.commit()
                    else:
                        print(f"Failed to refresh access token for user {cred.influencer_id}")
        else:
            print("No expired credentials found")
    except Exception as e:
        print(e)
    finally:
        db.close()