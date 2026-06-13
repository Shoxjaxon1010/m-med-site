import schedule
import time
import subprocess
import os

MMED_DIR = "C:\\mmed-api"

def send_daily_report():
    print("Отправляю ежедневный отчёт...")
    subprocess.run(
        ["python", "telegram_report.py"],
        cwd=MMED_DIR
    )

# Каждый день в 22:00
schedule.every().day.at("22:00").do(send_daily_report)

print("Планировщик запущен — отчёт отправляется каждый день в 22:00")
while True:
    schedule.run_pending()
    time.sleep(60)
