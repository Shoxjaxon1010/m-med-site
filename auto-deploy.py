import requests
import time
import re
import subprocess
import os

# ===== НАСТРОЙКИ =====
HTML_FILE = "C:\\mmed-api\\index.html"
REPO_DIR  = "C:\\mmed-api"
TOKEN_FILE = "C:\\mmed-api\\github_token.txt"

GITHUB_USER = "Shoxjaxon1010"
GITHUB_REPO = "m-med-site"

def get_github_url():
    # Токен читается из отдельного файла (не хранится в коде)
    with open(TOKEN_FILE, "r", encoding="utf-8") as f:
        token = f.read().strip()
    return f"https://{GITHUB_USER}:{token}@github.com/{GITHUB_USER}/{GITHUB_REPO}.git"

def get_ngrok_url():
    for i in range(10):
        try:
            r = requests.get("http://localhost:4040/api/tunnels", timeout=3)
            tunnels = r.json().get("tunnels", [])
            for t in tunnels:
                if t.get("proto") == "https":
                    return t["public_url"]
        except:
            print(f"Zhdu ngrok... ({i+1}/10)")
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
    print(f"index.html obnovlyon: {url}")

def push_to_github():
    os.chdir(REPO_DIR)
    github_url = get_github_url()
    subprocess.run(["git", "add", "index.html"], capture_output=True, text=True)
    r2 = subprocess.run(
        ["git", "commit", "-m", "auto: update ngrok URL"],
        capture_output=True, text=True
    )
    if "nothing to commit" in r2.stdout:
        print("Net izmeneniy dlya kommita")
        return True
    r3 = subprocess.run(
        ["git", "push", github_url, "main"],
        capture_output=True, text=True
    )
    if r3.returncode == 0:
        print("Sayt obnovlyon na GitHub -> Netlify!")
        return True
    else:
        print(f"Oshibka push: {r3.stderr}")
        return False

def main():
    print("=" * 40)
    print("  M-MED Auto-Deploy (GitHub)")
    print("=" * 40)
    print("\n[1/3] Poluchayu ngrok URL...")
    url = get_ngrok_url()
    if not url:
        print("Ne udalos poluchit ngrok URL. Zapushchen li ngrok?")
        return
    print(f"ngrok URL: {url}")
    print("\n[2/3] Obnovlyayu index.html...")
    update_html_with_url(url)
    print("\n[3/3] Push na GitHub...")
    success = push_to_github()
    if success:
        print("\nVsyo gotovo!")
        print(f"API: {url}")
        print("Sayt: https://m-med-site.netlify.app")
    print("\n" + "=" * 40)

if __name__ == "__main__":
    main()
