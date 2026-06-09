import requests
import time
import re
import hashlib

# ===== НАСТРОЙКИ =====
NETLIFY_TOKEN = "nfp_oMEZtQ1ds3Ld8cERa3QCgyctBsBRB2KFac2c"
SITE_ID       = "dc4575ed-83df-4f1f-9c9a-a4c660d231d3"
HTML_FILE     = "C:\\mmed-api\\index.html"

def get_ngrok_url():
    for i in range(10):
        try:
            r = requests.get("http://localhost:4040/api/tunnels", timeout=3)
            tunnels = r.json().get("tunnels", [])
            for t in tunnels:
                if t.get("proto") == "https":
                    return t["public_url"]
        except:
            print(f"Жду ngrok... ({i+1}/10)")
            time.sleep(2)
    return None

def update_html_with_url(url):
    with open(HTML_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    new_content = re.sub(
        r"const API_URL = 'https://[^']+';",
        f"const API_URL = '{url}';",
        content
    )
    with open(HTML_FILE, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"v index.html обновлён: {url}")
    return new_content

def deploy_to_netlify(html_content):
    file_hash = hashlib.sha1(html_content.encode("utf-8")).hexdigest()
    headers = {
        "Authorization": f"Bearer {NETLIFY_TOKEN}",
        "Content-Type": "application/json"
    }
    manifest = {"files": {"/index.html": file_hash}}
    r = requests.post(
        f"https://api.netlify.com/api/v1/sites/{SITE_ID}/deploys",
        headers=headers,
        json=manifest
    )
    if r.status_code not in [200, 201]:
        print(f"x Ошибка создания деплоя: {r.status_code} - {r.text}")
        return False

    deploy_id = r.json()["id"]
    required = r.json().get("required", [])
    print(f"v Деплой создан: {deploy_id}")

    if file_hash in required or required:
        upload_headers = {
            "Authorization": f"Bearer {NETLIFY_TOKEN}",
            "Content-Type": "text/html; charset=utf-8"
        }
        ru = requests.put(
            f"https://api.netlify.com/api/v1/deploys/{deploy_id}/files/index.html",
            headers=upload_headers,
            data=html_content.encode("utf-8")
        )
        if ru.status_code in [200, 201]:
            print("v index.html загружен на Netlify!")
        else:
            print(f"x Ошибка загрузки: {ru.status_code} - {ru.text}")
            return False

    print("v Сайт обновлён на Netlify!")
    return True

def main():
    print("=" * 40)
    print("  M-MED Auto-Deploy")
    print("=" * 40)

    print("\n[1/3] Получаю ngrok URL...")
    url = get_ngrok_url()
    if not url:
        print("x Не удалось получить ngrok URL. Запущен ли ngrok?")
        input("Нажми Enter для выхода...")
        return
    print(f"v ngrok URL: {url}")

    print("\n[2/3] Обновляю index.html...")
    html_content = update_html_with_url(url)

    print("\n[3/3] Деплою на Netlify...")
    success = deploy_to_netlify(html_content)

    if success:
        print("\nv Всё готово! Сайт работает с новым URL.")
        print(f"v API: {url}")
        print(f"v Сайт: https://m-med-site.netlify.app")

    print("\n" + "=" * 40)
    input("Нажми Enter для выхода...")

if __name__ == "__main__":
    main()
