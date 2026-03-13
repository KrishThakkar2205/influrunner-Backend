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
            "Authorization": "Bearer EAANLSkTxaEgBQZC6a5tIBZCzN3uQoNCenjzBHctbaI09IuNkwi9ULEPhN7Q5D9eMhXvTvCznXv4cesZBZA7FN6RNZBdZCsRchd2NwsJ4oz8byaDXeFDb6RxrSeaPi6R3iqQ7R9rJfVSuAPSknE7WSAYUBGCmxDUMF8vfgSP2quLa6jlqaMT3Yr3a3BzCNKaTeArkTBvx5yVshf2pTo7SyRpo2f9nVQapDIEA5Mi59aZC0cRl0GW4PwlUcV2AZAjHEGgFZA571kbPjzombLQxbluWPCaZB2Vs0MS4z1BX4e8wZDZD"
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
                        "body": f"Shoot Remainder\n\nDear Infleuncer you have shoot today of {shoot.brand_name} at {shoot.shoot_time} at {shoot.location}\n\nNotes of the Shoot {shoot.notes}"
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

        
