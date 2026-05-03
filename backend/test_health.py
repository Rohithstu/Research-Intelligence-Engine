import requests
import json

try:
    resp = requests.get("http://localhost:8000/cache")
    print("Status:", resp.status_code)
    print("Data:", resp.json())
except Exception as e:
    print("Error:", e)
