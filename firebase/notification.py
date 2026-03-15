import firebase_admin
from firebase_admin import credentials, messaging

def send_notification(token, title, body):
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        android=messaging.AndroidConfig(
            priority="high",  # ensures delivery even in doze mode
            notification=messaging.AndroidNotification(
                sound="default",       # ← Add this!
                channel_id="influrunner_main_v2",
                icon="ic_notification",       # ← custom icon
                color="#FF6B1A",  # ← Must match the channel ID we create
            ),
        ),
        token=token,
    )
    
    response = messaging.send(message)
    return True