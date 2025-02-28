import requests
import json

def get_token():
    with open('/data/options.json', 'r') as f:
        options = json.load(f)
    return options['HA_TOKEN']

def update_entity(entity_id, data_payload):
    token = get_token()
    if not token:
        print("No token found.")
        return None
    url = f"http://127.0.0.1:8123/api/states/{entity_id}"
    headers = {
        "Authorization": f"Bearer {get_token()}",
        "Content-Type": "application/json"
    }
    response = requests.post(url, headers=headers, data=json.dumps(data_payload))
    print(response.status_code)
    print(response.text)
    return response