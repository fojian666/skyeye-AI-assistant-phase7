import os, sys, re, requests, json
sys.path.insert(0, '/Users/chenguangxi/skyeye/skyeye')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gtus.settings')
import django
django.setup()
from rest_framework_jwt.utils import jwt_encode_handler, jwt_payload_handler
from django.contrib.auth import get_user_model
User = get_user_model()
user = User.objects.get(username='admin')
payload = jwt_payload_handler(user)
token = jwt_encode_handler(payload)

r = requests.post('http://127.0.0.1:8009/api/panorama/map_view_clue_list',
                  headers={'Authorization': f'Bearer {token}'},
                  json={'keyword':'','grid_name':'','status':''})

text = r.text
m = re.search(r'<title>(.*?)</title>', text)
if m: print('Error:', m.group(1))
