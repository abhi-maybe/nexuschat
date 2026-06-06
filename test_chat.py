#!/usr/bin/env python3
"""Test chat endpoint using stdlib only."""
import urllib.request
import json
import ssl

BASE = "https://nexuschat-dev.vercel.app"
ctx = ssl.create_default_context()

def api(method, path, data=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(f"{BASE}{path}", data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=20) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()
    except Exception as e:
        return 0, str(e)

# Register
status, body = api("POST", "/api/auth/register", {"username": "chattest999", "password": "test1234"})
print(f"Register: {status} {body[:200]}")
data = json.loads(body)
token = data.get("token", "")

# Stream chat xiaomi
print("\n=== Stream xiaomi ===")
status, body = api("POST", "/api/chat/send", {"message": "hello", "model": "mimo-v2-flash", "provider": "xiaomi", "stream": True}, token)
print(f"Status: {status}")
print(f"Body: {body[:500]}")

# Non-stream chat xiaomi
print("\n=== Non-stream xiaomi ===")
status, body = api("POST", "/api/chat/send", {"message": "hello", "model": "mimo-v2-flash", "provider": "xiaomi", "stream": False}, token)
print(f"Status: {status}")
print(f"Body: {body[:500]}")

# Stream openrouter
print("\n=== Stream openrouter ===")
status, body = api("POST", "/api/chat/send", {"message": "hello", "model": "openai/gpt-4o", "provider": "openrouter", "stream": True}, token)
print(f"Status: {status}")
print(f"Body: {body[:500]}")

# Stream deepseek
print("\n=== Stream deepseek ===")
status, body = api("POST", "/api/chat/send", {"message": "hello", "model": "deepseek-chat", "provider": "deepseek", "stream": True}, token)
print(f"Status: {status}")
print(f"Body: {body[:500]}")
