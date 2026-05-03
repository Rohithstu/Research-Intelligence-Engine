import requests
import json

payload = {
    "query": "transformer models",
    "max_results": 10
}

try:
    resp = requests.post("http://localhost:8000/search", json=payload, timeout=30)
    print("Status:", resp.status_code)
    if resp.status_code == 200:
        data = resp.json()
        print("Papers Found:", len(data.get("papers", [])))
        if len(data.get("papers", [])) > 0:
            print("First Paper:", data["papers"][0]["title"])
    else:
        print("Error Data:", resp.text)
except Exception as e:
    print("Error:", e)
