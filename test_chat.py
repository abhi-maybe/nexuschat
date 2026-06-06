#!/usr/bin/env python3
"""Test chat endpoint using stdlib only."""
import urllib.request
import json
import ssl
import random
import string

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

# Register with random username
username = "test" + "".join(random.choices(string.digits, k=6))
status, body = api("POST", "/api/auth/register", {"username": username, "password": "test1234"})
print(f"Register ({username}): {status} {body[:200]}")
data = json.loads(body)
token = data.get("token", "")

if not token:
    print("No token, exiting")
    exit(1)

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
