import firebase_admin
from firebase_admin import credentials, messaging

cred = credentials.Certificate("firebase/influrunner-78978-firebase-adminsdk-fbsvc-d1cb84dc2e.json")

firebase_admin.initialize_app(cred)