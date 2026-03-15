from models import Influencer, DeviceTokens, Credentials
from firebase.notification import send_notification
from database import SessionLocal

def connect_instagram():
    db = SessionLocal()
    try:
        result = (
            db.query(Influencer.id)
            .outerjoin(Credentials, Influencer.id == Credentials.influencer_id)
            .filter(Credentials.influencer_id == None)
            .all()
        )
        influencer_ids = [row[0] for row in result]
        for influencer_id in influencer_ids:
            device_token = db.query(DeviceTokens.device_token).filter(DeviceTokens.influencer_id == influencer_id).first()
            send_notification(device_token.device_token, "⚡ Don’t Leave Your Profile Incomplete", "Connect Instagram to unlock your full creator portfolio.")
    except Exception as e:
        print(e)
    finally:
        db.close()