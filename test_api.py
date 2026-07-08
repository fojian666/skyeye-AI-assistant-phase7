import base64, urllib.request, json

# Encrypt password
plain = 'admin123'
public_key = 'laiS2026pwd'
offset = 18
mix_str = plain + '|' + public_key
result = ''
for c in mix_str:
    result += chr(ord(c) + offset)
result = result[::-1]
encrypted = base64.b64encode(result.encode('latin-1')).decode()

# Login
data = json.dumps({"username": "admin", "password": encrypted}).encode()
req = urllib.request.Request("http://localhost:8009/api/system/login_check", data=data,
    headers={"Content-Type": "application/json"}, method="POST")
resp = json.loads(urllib.request.urlopen(req).read())
token = resp["tokens"]
print(f"Login OK, token[:30] = {token[:30]}")

# Test menu_list (GET)
req2 = urllib.request.Request("http://localhost:8009/api/system/menu_list",
    headers={"Authorization": f"Bearer {token}"})
try:
    resp2 = json.loads(urllib.request.urlopen(req2).read())
    print(f"menu_list: code={resp2['code']}, data_count={len(resp2.get('data', []))}")
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"menu_list HTTP {e.code}: {body}")
