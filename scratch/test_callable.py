import urllib.request
import json

regions = ['us-central1', 'europe-west1', 'asia-east1']
url_template = 'https://{region}-alley-d0944.cloudfunctions.net/getLevelProgress'

for region in regions:
    url = url_template.format(region=region)
    print(f"Testing {url}...")
    headers = {'Content-Type': 'application/json'}
    # Firebase callable expects JSON payload: {"data": {"level": "68"}}
    body = json.dumps({"data": {"level": "68"}}).encode('utf-8')
    req = urllib.request.Request(url, data=body, headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req) as resp:
            data = resp.read().decode('utf-8')
            print(f"SUCCESS ({region}):", data[:500])
            break
    except Exception as e:
        print(f"Failed ({region}):", e)
