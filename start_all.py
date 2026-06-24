import subprocess
import threading
import time
import re
import os

print("Starting HTTP server on port 8088...")
http_proc = subprocess.Popen(["python", "-m", "http.server", "8088"], cwd="webapp")

print("Starting localtunnel...")
lt_proc = subprocess.Popen(["npx", "localtunnel", "--port", "8088"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, shell=True)

url = None
for line in iter(lt_proc.stdout.readline, ''):
    print("LT:", line.strip())
    match = re.search(r'https://[\w-]+\.loca\.lt', line)
    if match:
        url = match.group(0)
        break
    if "your url is:" in line.lower():
        parts = line.split("your url is:")
        if len(parts) > 1:
            url = parts[1].strip()
            break

if not url:
    print("Failed to get localtunnel URL!")
    http_proc.kill()
    lt_proc.kill()
    exit(1)

print(f"Got URL: {url}")

print("Updating config.py...")
with open("config.py", "r", encoding="utf-8") as f:
    content = f.read()

new_content = re.sub(r'WEBAPP_URL\s*=\s*".*?"', f'WEBAPP_URL = "{url}"', content)
with open("config.py", "w", encoding="utf-8") as f:
    f.write(new_content)

print("Starting Telegram Bot...")
bot_proc = subprocess.Popen(["python", "main.py"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

def print_bot_output():
    for line in iter(bot_proc.stdout.readline, ''):
        print("BOT:", line.strip())

threading.Thread(target=print_bot_output, daemon=True).start()

try:
    bot_proc.wait()
except KeyboardInterrupt:
    pass
finally:
    http_proc.kill()
    lt_proc.kill()
    bot_proc.kill()
    print("All processes terminated.")
