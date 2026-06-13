import subprocess
import time
import requests
import os

MMED_DIR = "C:\\mmed-api"

def is_uvicorn_running():
    try:
        r = requests.get("http://localhost:8000", timeout=2)
        return True
    except:
        return False

def is_ngrok_running():
    try:
        r = requests.get("http://localhost:4040/api/tunnels", timeout=2)
        tunnels = r.json().get("tunnels", [])
        return len(tunnels) > 0
    except:
        return False

def start_uvicorn():
    subprocess.Popen(
        ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd=MMED_DIR,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    print("Uvicorn перезапущен!")
    time.sleep(5)

def start_ngrok():
    subprocess.Popen(
        ["ngrok.exe", "http", "8000"],
        cwd=MMED_DIR,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    print("Ngrok перезапущен!")
    time.sleep(10)
    # После перезапуска ngrok — обновляем сайт
    try:
        subprocess.run(
            ["python", "auto-deploy.py"],
            cwd=MMED_DIR,
            creationflags=subprocess.CREATE_NO_WINDOW,
            timeout=60
        )
        print("Сайт обновлён с новым ngrok URL!")
    except Exception as e:
        print(f"Ошибка обновления сайта: {e}")

print("Watchdog запущен — слежу за uvicorn и ngrok...")
while True:
    time.sleep(30)
    
    if not is_uvicorn_running():
        print("Uvicorn остановился — перезапускаю...")
        start_uvicorn()
    
    if not is_ngrok_running():
        print("Ngrok остановился — перезапускаю...")
        start_ngrok()
