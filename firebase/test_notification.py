from firebase_admin import messaging
import firebase_admin
from firebase_admin import credentials, messaging

cred = credentials.Certificate("influrunner-78978-firebase-adminsdk-fbsvc-d1cb84dc2e.json")

firebase_admin.initialize_app(cred)


message = messaging.Message(
    notification=messaging.Notification(
        title="Test Notification",
        body="This is a test notification",
    ),
    token="ebMaDnWSSK2K-Vi9ulPbTE:APA91bFyBbUpeDhvSOyA4QzK3fFr1BVgo1lCCBlQYXRprdfBO18B8Ls3WeMMZq1CL0XpFR2QFwZ64pZxU9Ss2O8nYcrbmJb22-QMb2NB2rF3FncG_mUeufE"
)
response = messaging.send(message)

print(response)