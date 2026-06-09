"""测试 AI 学伴多场景回复"""
import requests

BASE = "http://localhost:8000/api/v1"

# 登录
r = requests.post(f"{BASE}/auth/login", json={"email": "admin@ai4edu.com", "password": "admin123"})
token = r.json()["data"]["access_token"]
headers = {"Authorization": f"Bearer {token}"}

test_cases = [
    "我不会做二次函数题",
    "帮我制定一个学习计划",
    "数学好难啊，给我一些建议",
    "考试快到了，好紧张",
    "我想学习英语单词有什么好方法",
    "有什么高效的学习技巧",
]

print("=== AI 学伴对话测试 ===\n")
for msg in test_cases:
    r = requests.post(f"{BASE}/buddies/chat", json={"message": msg}, headers=headers)
    d = r.json()
    reply = d.get("data", {}).get("content", "ERROR")
    # 只显示前 80 字
    print(f"Q: {msg}")
    print(f"A: {reply[:100]}...")
    print()
