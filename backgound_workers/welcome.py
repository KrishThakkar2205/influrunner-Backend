from models import Influencer, DeviceTokens, Credentials
from firebase.notification import send_notification
from database import SessionLocal
from dotenv import load_dotenv
import os
import requests

load_dotenv()

ACCESS_TOKEN = os.getenv("WABA_TOKEN")
PHONE_NUMBER_ID = os.getenv("WABA_PHONE_NUMBER_ID")

url = f"https://graph.facebook.com/v25.0/{PHONE_NUMBER_ID}/messages"

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

def connect_instagram():
    db = SessionLocal()
    try:
        result = (
            db.query(Influencer.id, Influencer.phone_number, Influencer.name)
            .outerjoin(Credentials, Influencer.id == Credentials.influencer_id)
            .filter(Influencer.whatsapp_notification == True)
            .filter(Credentials.influencer_id == None)
            .all()
        )
        for influencer_id, phone_number, name in result:
            try:
                payload = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": phone_number,
                    "type": "template",
                    "template": {
                        "name": "connect_instagram",
                        "language": {
                            "code": "en"
                        },
                        "components": [
                            {
                                "type": "body",
                                "parameters": [
                                    {
                                        "type": "text",
                                        "parameter_name": "name",
                                        "text": name
                                    }
                                ]
                            }
                        ]
                    }
                }
                response = requests.post(
                    url,
                    headers=headers,
                    json=payload
                )

                if response.status_code == 200:
                    print(f"Successfully sent template message to {phone_number}")
                else:
                    print(f"Failed to send template message to {phone_number}")
                    print("Response:", response.text)
            except Exception as e:
                print(e)
    except Exception as e:
        print(e)
    finally:
        db.close()