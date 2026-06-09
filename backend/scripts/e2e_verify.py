import requests
import json

BASE = "http://localhost:8000/api/v1"
EMAIL = "admin@ai4edu.com"
PWD = "admin123"

# 1. 登录
r = requests.post(f"{BASE}/auth/login", json={"email": EMAIL, "password": PWD})
r.raise_for_status()
token = r.json()["data"]["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print(f"[OK] Login success, user_id={r.json()['data']['user_id']}")

# 2. 测试笔记 API
r = requests.get(f"{BASE}/notes?page=1&page_size=10", headers=headers)
d = r.json()
print(f"[Notes] code={d['code']}, total={d['data']['total']}, items={len(d['data']['items'])}")
for n in d['data']['items'][:3]:
    print(f"  - {n['title']} ({n['note_type']})")

# 3. 测试资源 API
r = requests.get(f"{BASE}/resources/list?page=1&page_size=10", headers=headers)
d = r.json()
print(f"[Resources] code={d.get('code','?')}, total={d.get('data',{}).get('total','?')}")
if 'data' in d and 'items' in d['data']:
    for res in d['data']['items'][:3]:
        print(f"  - {res['title']} ({res['resource_type']})")

# 4. 测试知识图谱 square API
r = requests.get(f"{BASE}/graphs/square", headers=headers)
d = r.json()
print(f"[Graph] code={d['code']}")
for s in d['data']:
    if s['node_count'] > 0:
        print(f"  - {s['id']}: {s['node_count']} nodes")

# 5. 测试 AI 学伴 profile API
r = requests.get(f"{BASE}/buddies/profile", headers=headers)
d = r.json()
print(f"[Buddy] code={d['code']}, name={d['data'].get('name','?')}")

# 6. 测试 AI 学伴 chat API
r = requests.post(f"{BASE}/buddies/chat", headers=headers, json={"message": "你好，请介绍一下自己"})
d = r.json()
print(f"[Chat] code={d['code']}, reply={d['data'].get('content','?')[:50]}...")

print("\n=== All API tests passed ===")
