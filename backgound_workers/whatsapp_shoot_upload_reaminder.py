from datetime import datetime, timedelta
from database import SessionLocal
from models import Shoots, Uploads
import requests

def send_shoot_upload_reminder():
    db = SessionLocal()
    try:
        url = "https://graph.facebook.com/v25.0/1025620817303779/messages"        
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer EAANhtEqdFqUBQZCYIZBWCMO9Mkr1ZBNZBghvkuRcO6XhcJAZAxec0Rn3Ur3dSH5bAo39R9WEZBcFEQmpGNjCW56jAp98TDKa2nbT3Ibp9R8LL91VolZBuybBisCztovTeLYfMB4bSLdKnsGb83CzoJb03rZAA7lBcdYYaQ64qjVWQZCWGZCD5fgSz81RxLx9tueBrDgUq8RbQsaFOZCM5Tt69rhtt1hfyoNbiU4j6UQbshbmiT1fc73Y2OQDDP2cFPZCxzH0kwj7hQaVDMXrRGmFQdv4"
        }
        now = datetime.utcnow().date()
        shoot = db.query(Shoots).filter(Shoots.shoot_date == now).first()
        if shoot:
            payload = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": "919099368070",
                    "type": "text",
                    "text": {
                        "preview_url": False,   # True if you want link preview
                        "body": f"*Shoot Remainder*\n\nDear Infleuncer you have shoot today of {shoot.brand_name} at {shoot.shoot_time} at {shoot.location}\n\nNotes of the Shoot : {shoot.notes}"
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

        
