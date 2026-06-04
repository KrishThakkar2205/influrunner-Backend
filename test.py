import requests
import json

ACCESS_TOKEN = "YOUR_PERMANENT_ACCESS_TOKEN"
PHONE_NUMBER_ID = "YOUR_PHONE_NUMBER_ID"





response = requests.post(
    url,
    headers=headers,
    json=payload
)

print("Status Code:", response.status_code)
print("Response Headers:", response.headers)
print("Response Text:")
print(response.text)

try:
    print("\nJSON Response:")
    print(json.dumps(response.json(), indent=2))
except Exception:
    print("\nResponse is not JSON")