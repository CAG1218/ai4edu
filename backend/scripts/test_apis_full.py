"""
完整 E2E 测试：登录 → 获取 token → 调用笔记/资源 API
"""
import json
import urllib.request
import urllib.error
import sys

# 修复 Windows GBK 终端的中文/Unicode 输出问题
sys.stdout.reconfigure(encoding='utf-8')

BASE = "http://localhost:8000"

def api(method, path, token=None, body=None):
    url = BASE + path
    req = urllib.request.Request(url, method=method)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    if body:
        req.add_header("Content-Type", "application/json")
        req.data = json.dumps(body).encode()
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"  [FAIL] HTTP {e.code}: {body[:200]}")
        return None
    except Exception as e:
        print(f"  [FAIL] {e}")
        return None

# 1. 登录
print("=== Login ===")
login_resp = api("POST", "/api/v1/auth/login", body={
    "email": "admin@ai4edu.com",
    "password": "admin123"
})
if not login_resp:
    print("Login failed, aborting")
    exit(1)

token = login_resp["data"]["access_token"]
nickname = login_resp["data"].get("nickname", "")
role = login_resp["data"].get("role", "")
print(f"  [OK] Login success: {nickname} ({role})")
print(f"  token prefix: {token[:20]}...")

# 2. 测试笔记 API
print("\n=== Notes API ===")
data = api("GET", "/api/v1/notes?page=1&page_size=5", token=token)
if data:
    print(f"  code: {data.get('code')}")
    d = data.get("data", {})
    if isinstance(d, dict):
        print(f"  total: {d.get('total', '?')}")
        items = d.get("items", [])
        print(f"  items: {len(items)}")
        for n in items[:5]:
            title = n.get("title", "")
            print(f"    - [{n.get('note_type')}] {title[:30]}")
    else:
        print(f"  data type: {type(d)}")
        print(f"  data: {d}")

# 3. 测试资源 API
print("\n=== Resources API ===")
data = api("GET", "/api/v1/resources/list?page=1&page_size=5", token=token)
if data:
    print(f"  code: {data.get('code')}")
    d = data.get("data", {})
    if isinstance(d, dict):
        print(f"  total: {d.get('total', '?')}")
        items = d.get("items", [])
        print(f"  items: {len(items)}")
        for r in items[:5]:
            title = r.get("title", "")
            print(f"    - [{r.get('resource_type')}] {title[:30]}")
    else:
        print(f"  data type: {type(d)}")
        print(f"  data: {d}")

print("\n=== Test Complete ===")
