import base64
import urllib.request
import json

plain = 'admin123'
public_key = 'laiS2026pwd'
offset = 18

mix_str = plain + '|' + public_key
result = ''
for c in mix_str:
    result += chr(ord(c) + offset)
result = result[::-1]
encrypted = base64.b64encode(result.encode('latin-1')).decode()

data = json.dumps({'username': 'admin', 'password': encrypted}).encode()
req = urllib.request.Request('http://localhost:8009/api/system/login_check', data=data,
    headers={'Content-Type': 'application/json'}, method='POST')
try:
    resp = urllib.request.urlopen(req)
    print('SUCCESS:', resp.read().decode())
except urllib.error.HTTPError as e:
    print('FAIL:', e.code, e.read().decode())
