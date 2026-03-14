from datetime import datetime, timedelta
from database import SessionLocal
from models import Shoots, Uploads,Influencer
from zoneinfo import ZoneInfo
import requests

def send_shoot_reminder_bfr_2hr():
    db = SessionLocal()
    try:
        url = "https://graph.facebook.com/v25.0/1025620817303779/messages"        
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer EAANhtEqdFqUBQymTuPHJNSiC1DYTHQo1Oq3t8ZB9QZAhDpr4s0mI64adoWNEQrI01fV5H41yTBg8uRc7S4ysjgJNRGdxiXmTezmkGgCkK6A9JRRrzEZBTFj5YTbtcvV6JZARaESI4DZBA7aNEMqgLWKWefPsVKh2QzbFZCXwu38WbxdonTLgY8IboZAHqXsFBAfrJeoFyX5SvxdbrooeyXhP5L9sveH0mhg3Quev2ugsZCsRhsPpYNz3SI7NO5vSRjZAkowf4E9cXIeGFLINbZAaAEOwZDZD"
        }
        now = datetime.utcnow()
        # time = datetime.utcnow().time()

        shoots = db.query(Shoots).filter(Shoots.shoot_date == now.date(), Shoots.completed == False, Shoots.notify_before_2hr == False).all()
        for shoot in shoots:
            shoot_date_time = datetime.combine(shoot.shoot_date, shoot.shoot_time)
            diff = shoot_date_time - now
            ist_time = shoot_date_time.astimezone(ZoneInfo("Asia/Kolkata"))
            formatted_time = ist_time.strftime("%I:%M %p")
            if timedelta(hours=1, minutes=55) <= diff <= timedelta(hours=2):
                infleuncer = db.query(Influencer.name, Influencer.phone_number).filter(Influencer.id == shoot.influencer_id).first()
                payload = { 
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": infleuncer.phone_number,
                    "type": "text",
                    "text": {
                        "preview_url": False,   # True if you want link preview
                        "body": f"*Shoot Remainder*\n\nDear {infleuncer.name} you have shoot today\n\nBrand Name : {shoot.brand_name}\nShoot Time : {formatted_time}\nLocation : {shoot.location}\n\nNotes : {shoot.notes}\n\nBe On time\nThis notification is sent 2 hours before the shoot\n\nInfluRunner Team"
                    }
                }
                response = requests.post(url, headers=headers, json=payload)
                if response.status_code != 200:
                    print(f"Failed to send shoot upload reminder for shoot {shoot.id}")
                else:
                    shoot.notify_before_2hr = True
                    db.commit()
    except Exception as e:
        print(e)
    finally:
        db.close()

        
