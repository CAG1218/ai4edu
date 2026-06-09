"""
快速测试笔记和资源 API
"""
import json
import urllib.request
import urllib.error

TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOjEsInJvbGUiOiJzdHVkZW50IiwidGVuYW50X2lkIjozLCJleHAiOjE3ODA1NDMxMzMsInR5cGUiOiJhY2Nlc3MifQ.EWRw5UI8OrKrP60cm73_idSOJk04lEEdQjvhcDYfK6w"

def api_get(path):
    url = f"http://localhost:8000{path}"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            return data
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"  HTTP {e.code}: {body[:200]}")
        return None
    except Exception as e:
        print(f"  Error: {e}")
        return None

print("=== 测试笔记 API ===")
data = api_get("/api/v1/notes?page=1&page_size=10")
if data:
    print(f"  code: {data.get('code')}")
    d = data.get("data", {})
    if isinstance(d, dict):
        print(f"  total: {d.get('total')}")
        items = d.get("items", [])
        print(f"  items count: {len(items)}")
        for n in items[:3]:
            print(f"    - {n.get('title')} (id={n.get('id')})")
    else:
        print(f"  data type: {type(d)}")

print()
print("=== 测试资源 API ===")
data = api_get("/api/v1/resources/list?page=1&page_size=10")
if data:
    print(f"  code: {data.get('code')}")
    d = data.get("data", {})
    if isinstance(d, dict):
        print(f"  total: {d.get('total')}")
        items = d.get("items", [])
        print(f"  items count: {len(items)}")
        for r in items[:3]:
            print(f"    - {r.get('title')} (id={r.get('id')})")
    else:
        print(f"  data type: {type(d)}")
        print(f"  data: {d}")
