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
                device_token = db.query(DeviceTokens.device_token).filter(DeviceTokens.influencer_id == shoot.influencer_id).all()
                for token in device_token:
                    try:
                        status = send_notification(token.device_token, "Shoot Remainder Before 2 hour", f"Brand Name : {shoot.brand_name}\nShoot Time : {formatted_time}\nLocation : {shoot.location}\n\nNotes : {shoot.notes}\n\nBe On time")
                        if status != 200:
                            print(f"Failed to send shoot upload reminder for shoot {shoot.id}")
                        else:
                            shoot.notify_before_2hr = True
                            db.commit()
                    except Exception as e:
                        print(e)
                # payload = { 
                #     "messaging_product": "whatsapp",
                #     "recipient_type": "individual",
                #     "to": infleuncer.phone_number,
                #     "type": "text",
                #     "text": {
                #         "preview_url": True,   # True if you want link preview
                #         "body": f"*Shoot Remainder*\n\nDear {infleuncer.name} you have shoot today\n\nBrand Name : {shoot.brand_name}\nShoot Time : {formatted_time}\nLocation : {shoot.location}\n\nNotes : {shoot.notes}\n\nBe On time\nThis notification is sent 2 hours before the shoot\n\nInfluRunner Team\nhttps://influrunner.com/influencer/schedule"
                #     }
                # }
                # response = requests.post(url, headers=headers, json=payload)
    except Exception as e:
        print(e)
    finally:
        db.close()

def send_shoot_reminder_bfr_1hr():
    db = SessionLocal()
    try:
        # url = "https://graph.facebook.com/v25.0/1025620817303779/messages"        
        # headers = {
        #     "Content-Type": "application/json",
        #     "Authorization": f"Bearer {access_token_for_waba}"
        # }
        now = datetime.utcnow()
        # time = datetime.utcnow().time()

        shoots = db.query(Shoots).filter(Shoots.shoot_date == now.date(), Shoots.completed == False, Shoots.notify_before_1hr == False).all()
        for shoot in shoots:
            shoot_date_time = datetime.combine(shoot.shoot_date, shoot.shoot_time)
            diff = shoot_date_time - now
            ist_time = shoot_date_time.astimezone(ZoneInfo("Asia/Kolkata"))
            formatted_time = ist_time.strftime("%I:%M %p")
            if timedelta(minutes=55) <= diff <= timedelta(hours=1):
                infleuncer = db.query(Influencer.name, Influencer.phone_number).filter(Influencer.id == shoot.influencer_id).first()
                device_token = db.query(DeviceTokens.device_token).filter(DeviceTokens.influencer_id == shoot.influencer_id).all()
                for token in device_token:
                    try:
                        status = send_notification(token.device_token, "Shoot Remainder Before 1 hour", f"Brand Name : {shoot.brand_name}\nShoot Time : {formatted_time}\nLocation : {shoot.location}\n\nNotes : {shoot.notes}\n\nBe On time")
                    
                # payload = { 
                #     "messaging_product": "whatsapp",
                #     "recipient_type": "individual",
                #     "to": infleuncer.phone_number,
                #     "type": "text",
                #     "text": {
                #         "preview_url": True,   # True if you want link preview
                #         "body": f"*Shoot Remainder*\n\nDear {infleuncer.name} you have shoot today\n\nBrand Name : {shoot.brand_name}\nShoot Time : {formatted_time}\nLocation : {shoot.location}\n\nNotes : {shoot.notes}\n\nBe On time\nThis notification is sent 1 hour before the shoot\n\nInfluRunner Team\nhttps://influrunner.com/influencer/schedule"
                #     }
                # }
                # response = requests.post(url, headers=headers, json=payload)
                        if status != 200:
                            print(f"Failed to send shoot upload reminder for shoot {shoot.id}")
                        else:
                            shoot.notify_before_1hr = True
                            db.commit()
                    except Exception as e:
                        print(e)
    except Exception as e:
        print(e)
    finally:
        db.close()