import requests
import json

def get_token():
    default_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI2YzhmOTI5ZmI0YTM0N2MzYjllYzFhNjIxOTIyYjkxNyIsImlhdCI6MTc0MDU0MzQ0NiwiZXhwIjoyMDU1OTAzNDQ2fQ.1NXpUA0LA8Jwa63egiLptQpo6yRdbwEFQ1-GlGk50TI'
    with open('/data/options.json', 'r') as f:
        options = json.load(f)
    return options['HA_TOKEN'] or default_token

def update_entity(entity_id, data_payload):
    url = f"http://127.0.0.1:8123/api/states/{entity_id}"
    headers = {
        "Authorization": f"Bearer {get_token()}",
        "Content-Type": "application/json"
    }
    response = requests.post(url, headers=headers, data=json.dumps(data_payload))
    return response