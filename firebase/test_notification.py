import firebase_admin
from firebase_admin import credentials, messaging

# ---- STEP 1: Check if already initialized (avoids duplicate app error) ----
if not firebase_admin._apps:
    cred = credentials.Certificate("influrunner-78978-firebase-adminsdk-fbsvc-393d319de2.json")
    firebase_admin.initialize_app(cred)
    print("✅ Firebase initialized successfully")
else:
    print("⚠️  Firebase was already initialized")

# ---- STEP 2: Paste your FRESH token here ----
FCM_TOKEN = "f7MDoft5S5upYi_uySsaQz:APA91bGFIkrwBLDjp-qBCvlm1zQ5a2zLFI0b1V5XP0wQP1mV-fJz1og1TckDnn1UYTd-evwG1__aY5jv6BdseMk2VFxVXciK6nbIx0GfCGCF-SlyDhjCPxw"
# ---- STEP 3: Validate token format before sending ----
if not FCM_TOKEN:
    print("❌ ERROR: You forgot to paste your fresh FCM token!")
    exit(1)

if ":" not in FCM_TOKEN:
    print("❌ ERROR: Token format looks wrong — should contain a ':' character")
    exit(1)

print(f"📱 Sending to token: {FCM_TOKEN[:20]}...")

# ---- STEP 4: Send with detailed error handling ----
try:
    message = messaging.Message(
        notification=messaging.Notification(
            title="Test Notification",
            body="This is a test notification",
        ),
        android=messaging.AndroidConfig(
            priority="high",  # ensures delivery even in doze mode
            notification=messaging.AndroidNotification(
                sound="default",       # ← Add this!
                default_sound=True,      # 👈 add this line
                default_vibrate_timings=True,
                default_light_settings=True,
                channel_id="influrunner_main_v3",
                icon="ic_notification",       # ← custom icon
                color="#FF6B1A",  # ← Must match the channel ID we create
            ),
        ),
        token=FCM_TOKEN,
    )

    response = messaging.send(message)
    print(f"✅ Notification sent successfully! Message ID: {response}")

except messaging.UnregisteredError:
    print("❌ ERROR: Token is unregistered — app was uninstalled or token expired. Get a fresh token from your app.")

except messaging.SenderIdMismatchError:
    print("❌ ERROR: Sender ID mismatch — your google-services.json in the app does NOT match this Firebase project. Re-download google-services.json from Firebase console and rebuild your APK.")

except messaging.InvalidArgumentError as e:
    print(f"❌ ERROR: Invalid argument — {e}")

except firebase_admin.exceptions.InvalidArgumentError as e:
    print(f"❌ ERROR: Firebase invalid argument — {e}")

except Exception as e:
    print(f"❌ UNEXPECTED ERROR: {type(e).__name__}: {e}")
