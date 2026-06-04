from datetime import datetime, timedelta
from database import SessionLocal
from firebase.notification import send_notification
from models import Shoots, Uploads,Influencer, DeviceTokens
from zoneinfo import ZoneInfo
import os
from dotenv import load_dotenv
import requests

load_dotenv()

ACCESS_TOKEN = os.getenv("WABA_TOKEN")
PHONE_NUMBER_ID = os.getenv("WABA_PHONE_NUMBER_ID")

url = f"https://graph.facebook.com/v25.0/{PHONE_NUMBER_ID}/messages"

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

def send_shoot_reminder_bfr_2hr():
    db = SessionLocal()
    try:
        now = datetime.utcnow().replace(tzinfo=ZoneInfo("UTC"))
        print(f"[2HR] Current UTC time: {now}")

        shoots = db.query(Shoots).filter(
            Shoots.shoot_date == now.date(),
            Shoots.completed == False,
            Shoots.notify_before_2hr == False
        ).all()
        
        print(f"[2HR] Shoots found for today: {len(shoots)}")  # ✅ check if shoots are being fetched

        for shoot in shoots:
            shoot_date_time = datetime.combine(shoot.shoot_date, shoot.shoot_time)
            shoot_date_time_utc = shoot_date_time.replace(tzinfo=ZoneInfo("UTC"))
            diff = shoot_date_time_utc - now
            ist_time = shoot_date_time_utc.astimezone(ZoneInfo("Asia/Kolkata"))
            formatted_time = ist_time.strftime("%I:%M %p")

            print(f"[2HR] Shoot ID: {shoot.id} | UTC time: {shoot_date_time_utc} | IST: {formatted_time} | Diff: {diff}")  # ✅ check diff value

            if timedelta(hours=1, minutes=55) <= diff <= timedelta(hours=2):
                print(f"[2HR] ✅ Shoot {shoot.id} is within 2hr window, sending notification...")
                # device_tokens = db.query(DeviceTokens.device_token).filter(
                #     DeviceTokens.influencer_id == shoot.influencer_id
                # ).all()
                infleuncer_details = db.query(Influencer.name, Influencer.phone_number).filter(
                    Influencer.id == shoot.influencer_id
                ).first()
                
                if not infleuncer_details:
                    print(f"[2HR] ❌ Influencer not found for shoot ID {shoot.id} with influencer_id {shoot.influencer_id}")
                    continue
                
                try:
                    payload_for_shoot_remainder = {
                        "messaging_product": "whatsapp",
                        "to": infleuncer_details.phone_number,
                        "type": "template",
                        "template": {
                            "name": "shoot_remainder",
                            "language": {
                                "code": "en"
                            },
                            "components": [
                                {
                                    "type" : "header",
                                    "parameters": [
                                        {
                                            "type": "text",
                                            "parameter_name": "hour",
                                            "text": "2 Hours"
                                        }
                                    ]
                                },
                                {
                                    "type": "body",
                                    "parameters": [
                                        {
                                            "type": "text",
                                            "parameter_name": "name",
                                            "text": infleuncer_details.name
                                        },{
                                            "type": "text",
                                            "parameter_name": "brand_name",
                                            "text": shoot.brand_name
                                        },{
                                            "type": "text",
                                            "parameter_name": "shoot_date",
                                            "text": shoot_date_time.strftime("%d %B %Y")
                                        },{
                                            "type": "text",
                                            "parameter_name": "shoot_time",
                                            "text": formatted_time
                                        },{
                                            "type": "text",
                                            "parameter_name": "notes",
                                            "text": shoot.notes
                                        },{
                                            "type":"text",
                                            "parameter_name":"location",
                                            "text":shoot.location
                                        }
                                    ]
                                }
                            ]
                        }
                    }

                    response = requests.post(
                    url,
                    headers=headers,
                    json=payload_for_shoot_remainder
                    )
                
                    print(response.json())
                except Exception as e:
                    print(f"[2HR] ❌ Exception: {e}")

                shoot.notify_before_2hr = True
                db.commit()
            else:
                print(f"[2HR] ⏭ Shoot {shoot.id} NOT in window. Diff={diff}")  # ✅ tells you why it was skipped

    except Exception as e:
        print(f"[2HR] ❌ Outer exception: {e}")
    finally:
        db.close()

def send_shoot_reminder_bfr_1hr():
    db = SessionLocal()
    try:
        now = datetime.utcnow().replace(tzinfo=ZoneInfo("UTC"))
        shoots = db.query(Shoots).filter(Shoots.shoot_date == now.date(), Shoots.completed == False, Shoots.notify_before_1hr == False).all()
        for shoot in shoots:
            shoot_date_time = datetime.combine(shoot.shoot_date, shoot.shoot_time)
            shoot_date_time_utc = shoot_date_time.replace(tzinfo=ZoneInfo("UTC"))
            diff = shoot_date_time_utc - now
            ist_time = shoot_date_time_utc.astimezone(ZoneInfo("Asia/Kolkata"))
            formatted_time = ist_time.strftime("%I:%M %p")
            if timedelta(minutes=55) <= diff <= timedelta(hours=1):
                infleuncer_details = db.query(Influencer.name, Influencer.phone_number).filter(
                    Influencer.id == shoot.influencer_id
                ).first()
                
                if not infleuncer_details:
                    print(f"[1HR] ❌ Influencer not found for shoot ID {shoot.id} with influencer_id {shoot.influencer_id}")
                    continue
                
                try:
                    payload_for_shoot_remainder = {
                        "messaging_product": "whatsapp",
                        "to": infleuncer_details.phone_number,
                        "type": "template",
                        "template": {
                            "name": "shoot_remainder",
                            "language": {
                                "code": "en"
                            },
                            "components": [
                                {
                                    "type" : "header",
                                    "parameters": [
                                        {
                                            "type": "text",
                                            "parameter_name": "hour",
                                            "text": "1 Hours"
                                        }
                                    ]
                                },
                                {
                                    "type": "body",
                                    "parameters": [
                                        {
                                            "type": "text",
                                            "parameter_name": "name",
                                            "text": infleuncer_details.name
                                        },{
                                            "type": "text",
                                            "parameter_name": "brand_name",
                                            "text": shoot.brand_name
                                        },{
                                            "type": "text",
                                            "parameter_name": "shoot_date",
                                            "text": shoot_date_time.strftime("%d %B %Y")
                                        },{
                                            "type": "text",
                                            "parameter_name": "shoot_time",
                                            "text": formatted_time
                                        },{
                                            "type": "text",
                                            "parameter_name": "notes",
                                            "text": shoot.notes
                                        },{
                                            "type":"text",
                                            "parameter_name":"location",
                                            "text":shoot.location
                                        }
                                    ]
                                }
                            ]
                        }
                    }

                    response = requests.post(
                    url,
                    headers=headers,
                    json=payload_for_shoot_remainder
                    )
                
                    print(response.json())
                except Exception as e:
                    print(e)
                shoot.notify_before_1hr = True
                db.commit()
    except Exception as e:
        print(e)
    finally:
        db.close()