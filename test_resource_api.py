import os, sys
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

r = requests.get('http://127.0.0.1:8009/api/resource/resources/get_resources_on_one_map',
                 headers={'Authorization': f'Bearer {token}'})
print('code:', r.json().get('code'))
print('msg:', r.json().get('msg'))
