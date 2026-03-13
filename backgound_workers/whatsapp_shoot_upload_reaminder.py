from datetime import datetime, timedelta
from database import SessionLocal
from models import Shoots, Uploads
import requests

def send_shoot_upload_reminder():
    db = SessionLocal()
    try:
        url = "https://graph.facebook.com/v25.0/948781308327986/messages"        
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer <ACCESS_TOKEN>"
        }
        now = datetime.utcnow().date()
        shoots = db.query(Shoots).filter(Shoots.shoot_date == now).first()
        if shoots:
            payload = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": "919099368070",
                    "type": "text",
                    "text": {
                        "preview_url": False,   # True if you want link preview
                        "body": "Shoot Remainder\n\nDear Infleuncer you have shoot today at {shoot.shoot_time} at {shoot.location}"
                    }
                }
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code != 200:
                print(f"Failed to send shoot upload reminder for shoot {shoot.id}")
        else:
            print("No shoots found for today")
    except Exception as e:
        print(e)
    finally:
        db.close()

        
