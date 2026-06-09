#!/usr/bin/env python3
"""
Chạy script này 1 lần sau khi deploy lên Vercel để đăng ký webhook.
Usage:
  set BOT_TOKEN=xxxx      (Windows PowerShell: $env:BOT_TOKEN="xxxx")
  python setup_webhook.py https://your-project.vercel.app
Hoặc truyền token làm tham số thứ 2:
  python setup_webhook.py https://your-project.vercel.app <BOT_TOKEN>
"""
import os
import sys
import urllib.request
import json

if len(sys.argv) < 2:
    print("Usage: python setup_webhook.py https://your-project.vercel.app [BOT_TOKEN]")
    sys.exit(1)

BOT_TOKEN = sys.argv[2] if len(sys.argv) > 2 else os.environ.get("BOT_TOKEN", "")
if not BOT_TOKEN:
    print("❌ Thiếu BOT_TOKEN. Đặt $env:BOT_TOKEN hoặc truyền làm tham số thứ 2.")
    sys.exit(1)

base_url = sys.argv[1].rstrip("/")
webhook_url = f"{base_url}/api/webhook"

url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
data = json.dumps({"url": webhook_url}).encode()
req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

with urllib.request.urlopen(req) as r:
    result = json.loads(r.read())
    print(f"Response: {result}")
    if result.get("ok"):
        print(f"✅ Webhook đã được đăng ký: {webhook_url}")
    else:
        print(f"❌ Lỗi: {result.get('description')}")
