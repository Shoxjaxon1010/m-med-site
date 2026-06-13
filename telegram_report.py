import pyodbc
import requests
from datetime import date

# ===== НАСТРОЙКИ =====
BOT_TOKEN = "8630042512:AAHfsss3EQ-b9EIgqIe2KRpqg8Pb3qyvPR8"
CHAT_ID   = "7137922888"

DB_SERVER = "localhost"
DB_GLOBAL = "NGLOBAL"
DB_USER   = "sa"
DB_PASS   = "1"

BRANCH_NAMES = {
    3: "Bolalar shifoxonasi",
    4: "Sevinch Klinika",
    6: "Yangiariq",
}

def get_conn():
    return pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=" + DB_SERVER + ";"
        "DATABASE=" + DB_GLOBAL + ";"
        "UID=" + DB_USER + ";"
        "PWD=" + DB_PASS + ";"
    )

def get_today_stats():
    today = date.today().strftime("%Y-%m-%d")
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT I.OTDEL, COUNT(I.ID) as CHEKLAR, SUM(I.SUMMA) as SUMMA
        FROM INVOICE I
        WHERE CAST(I.DATAENTER as DATE) = '""" + today + """'
          AND I.SUMMA > 0
          AND I.OTDEL IN (3, 4, 6)
        GROUP BY I.OTDEL
        ORDER BY SUMMA DESC
    """)
    branches = cursor.fetchall()
    conn.close()
    return branches

def fmt(n):
    return f"{int(n):,}".replace(",", " ") + " so'm"

def send_report():
    try:
        branches = get_today_stats()
        today = date.today().strftime("%d.%m.%Y")

        msg = f"📊 <b>M-MED — Kunlik hisobot</b>\n"
        msg += f"📅 {today}\n"
        msg += "━━━━━━━━━━━━━━━━\n\n"
        msg += "<b>Filiallar bo'yicha:</b>\n\n"

        total_summa = 0
        total_count = 0

        for row in branches:
            otdel = row[0]
            count = row[1]
            summa = float(row[2]) if row[2] else 0
            total_summa += summa
            total_count += count
            branch_name = BRANCH_NAMES.get(otdel, f"Filial {otdel}")
            msg += f"<b>{branch_name}</b>\n"
            msg += f"   {count} chek — {fmt(summa)}\n\n"

        msg += "━━━━━━━━━━━━━━━━\n"
        msg += f"💰 <b>Jami bugun: {fmt(total_summa)}</b>\n"
        msg += f"📦 Jami: {total_count} chek\n"
        msg += "━━━━━━━━━━━━━━━━\n"
        msg += "🔗 m-med-site.netlify.app/kpi.html"

        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={
                "chat_id": CHAT_ID,
                "text": msg,
                "parse_mode": "HTML"
            }
        )
        print("Отчёт отправлен!")
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    send_report()
