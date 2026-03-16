from datetime import datetime, timedelta
from database import SessionLocal
from firebase.notification import send_notification
from models import Shoots, Uploads,Influencer, DeviceTokens
from zoneinfo import ZoneInfo
import requests


access_token_for_waba = "EAANhtEqdFqUBQZC2TnvE5xqZBglHEKehpxzZAabMCSFxkZA624fkq6ZBoiu333RjhbzGTfnEAJe73czUx72dqJL4Oy6UV4ok9WhtGCr3jemTNf55Hdkc2kJhlFJeGzQh9ZBoznGFTyFU2sxIeuglMxPwLlW5DzyaVb1IEv25L8bouctVr8eOyuNZBObyf2jJNgGrxxmrG2ZAXg7Ojqdvzd6ZCuzd4SlERtucnHSfpfGiRMz9paDCl6sxXFDIcii0cBZB1uCPF6dBsveIBxKIlcAD6i"

def send_shoot_reminder_bfr_2hr():
    db = SessionLocal()
    try:
        # url = "https://graph.facebook.com/v25.0/1025620817303779/messages"        
        # headers = {
        #     "Content-Type": "application/json",
        #     "Authorization": f"Bearer {access_token_for_waba}"
        # }
        now = datetime.utcnow().replace(tzinfo=ZoneInfo("UTC"))
        # time = datetime.utcnow().time()

        shoots = db.query(Shoots).filter(Shoots.shoot_date == now.date(), Shoots.completed == False, Shoots.notify_before_2hr == False).all()
        for shoot in shoots:
            shoot_date_time = datetime.combine(shoot.shoot_date, shoot.shoot_time)
            shoot_date_time_utc = shoot_date_time.replace(tzinfo=ZoneInfo("UTC"))
            diff = shoot_date_time_utc - now
            ist_time = shoot_date_time.astimezone(ZoneInfo("Asia/Kolkata"))
            formatted_time = ist_time.strftime("%I:%M %p")

            if timedelta(hours=1, minutes=55) <= diff <= timedelta(hours=2):
                influencer = db.query(Influencer.name, Influencer.phone_number).filter(Influencer.id == shoot.influencer_id).first()
                device_tokens = db.query(DeviceTokens.device_token).filter(DeviceTokens.influencer_id == shoot.influencer_id).all()

                all_sent = True  # Track if at least one succeeded
                for token in device_tokens:
                    try:
                        status = send_notification(
                            token.device_token,
                            "Shoot Reminder Before 2 Hours",
                            f"Brand Name : {shoot.brand_name}\nShoot Time : {formatted_time}\nLocation : {shoot.location}\n\nNotes : {shoot.notes}\n\nBe On time"
                        )
                        if status != 200:
                            print(f"Failed to send notification for shoot {shoot.id}, token {token.device_token}")
                            all_sent = False
                    except Exception as e:
                        print(f"Exception for shoot {shoot.id}: {e}")
                        all_sent = False

                # ✅ Set flag AFTER the loop, outside try/except of individual tokens
                # Mark as notified even if some tokens failed — prevents infinite retries
                shoot.notify_before_2hr = True
                db.commit()
    except Exception as e:
        print(e)
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
            ist_time = shoot_date_time.astimezone(ZoneInfo("Asia/Kolkata"))
            formatted_time = ist_time.strftime("%I:%M %p")
            if timedelta(minutes=55) <= diff <= timedelta(hours=1):
                infleuncer = db.query(Influencer.name, Influencer.phone_number).filter(Influencer.id == shoot.influencer_id).first()
                device_token = db.query(DeviceTokens.device_token).filter(DeviceTokens.influencer_id == shoot.influencer_id).all()
                for token in device_token:
                    try:
                        status = send_notification(token.device_token, "Shoot Remainder Before 1 hour", f"Brand Name : {shoot.brand_name}\nShoot Time : {formatted_time}\nLocation : {shoot.location}\n\nNotes : {shoot.notes}\n\nBe On time")
                        if status != 200:
                            print(f"Failed to send shoot upload reminder for shoot {shoot.id}")
                    except Exception as e:
                        print(e)
                shoot.notify_before_1hr = True
                db.commit()
    except Exception as e:
        print(e)
    finally:
        db.close()