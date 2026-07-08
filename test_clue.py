import os, sys, json
sys.path.insert(0, '/Users/chenguangxi/skyeye/skyeye')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gtus.settings')
import django
django.setup()

from rest_framework_jwt.utils import jwt_encode_handler, jwt_payload_handler
from django.contrib.auth import get_user_model
import requests

User = get_user_model()
user = User.objects.get(username='admin')
payload = jwt_payload_handler(user)
token = jwt_encode_handler(payload)

# Simulate frontend formInfo (what the browser actually sends)
body = {
    "keyword": "",
    "grid_name": "",
    "status": "",
    "startDate": "",
    "endDate": "",
    "page": 1,
    "limit": 5,
    "dataRange": [],
    "statusList": [0, 2, 5]
}

r = requests.post('http://127.0.0.1:8009/api/panorama/map_view_clue_list',
                  headers={'Authorization': f'Bearer {token}'},
                  json=body)
print('HTTP status:', r.status_code)
print('Response:', json.dumps(r.json(), indent=2, ensure_ascii=False))
