import requests

try:
    resp = requests.post(
        "http://127.0.0.1:8000/auth/register",
        json={"username": "test_curl", "email": "test_curl@test.com", "password": "123"},
        timeout=10
    )
    print("Status:", resp.status_code)
    print("Response:", resp.text)
except Exception as e:
    print("Request failed:", e)
