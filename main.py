from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from pydantic import BaseModel
import pyodbc
import json
import os
from datetime import datetime, date

SETTINGS_FILE = "C:\\mmed-api\\kpi_settings.json"

def load_settings_from_file():
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except:
        pass
    return {}

def save_settings_to_file(settings):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Ошибка сохранения настроек: {e}")

HISTORY_FILE = "C:\\mmed-api\\kpi_history.json"

def load_history():
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except:
        pass
    return {}

def save_history(history):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Ошибка сохранения истории: {e}")

KPI_HISTORY = load_history()

app = FastAPI(title="M-MED API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_SERVER  = "localhost"
DB_NAME    = "NAPTSKLAD"
DB_GLOBAL  = "NGLOBAL"
DB_USER    = "sa"
DB_PASS    = "1"

BRANCHES = {
    3: {"name_uz": "Bolalar shifoxonasi", "name_ru": "Детская больница"},
    4: {"name_uz": "Sevinch Klinika",     "name_ru": "Севинч Клиника"},
    6: {"name_uz": "Yangiariq",           "name_ru": "Янгиарик"},
}

# Пользователи KPI
KPI_USERS = {
    "adm":      {"name": "Администратор", "role": "admin",       "branch": None, "db_name": None},
    "5707":     {"name": "Дилафруз",      "role": "pharmacist",  "branch": 4,    "db_name": "Дилафруз"},
    "laylo":    {"name": "Лайло",         "role": "pharmacist",  "branch": 4,    "db_name": "Лайло"},
    "8994":     {"name": "Зебо",          "role": "pharmacist",  "branch": 3,    "db_name": "Зебо"},
    "жавохир":  {"name": "Жавохир",       "role": "pharmacist",  "branch": 3,    "db_name": "Жавохир"},
    "dilnura":  {"name": "Dilnura",       "role": "pharmacist",  "branch": 3,    "db_name": "Dilnura"},
    "gulyor":   {"name": "Gulyor",        "role": "pharmacist",  "branch": 6,    "db_name": "Gulyor"},
    "guljahon": {"name": "Guljahon",      "role": "pharmacist",  "branch": 6,    "db_name": "Guljahon"},
    "guli":     {"name": "Guli",          "role": "pharmacist",  "branch": 6,    "db_name": "Guli"},
    "oydinoy":  {"name": "Oydinoy",       "role": "pharmacist",  "branch": 6,    "db_name": "Oydinoy"},
    "sevinch":  {"name": "Sevinch",       "role": "pharmacist",  "branch": 6,    "db_name": "Sevinch"},
    "sevinch2": {"name": "Sevinch 2",     "role": "pharmacist",  "branch": 6,    "db_name": "Sevinch"},
    "dilfuza":  {"name": "Dilfuza",       "role": "pharmacist",  "branch": 6,    "db_name": "Dilfuza"},
}

KPI_PASSWORD_ADMIN = "123"
KPI_PASSWORD_STAFF = "12345678"

# Настройки KPI — загружаются из файла при старте
DEFAULT_SETTINGS = {
    "Дилафруз": {"fix": 0, "percent": 0, "plan": 0},
    "Лайло":    {"fix": 0, "percent": 0, "plan": 0},
    "Зебо":     {"fix": 0, "percent": 0, "plan": 0},
    "Жавохир":  {"fix": 0, "percent": 0, "plan": 0},
    "Dilnura":  {"fix": 0, "percent": 0, "plan": 0},
    "Gulyor":   {"fix": 0, "percent": 0, "plan": 0},
    "Guljahon": {"fix": 0, "percent": 0, "plan": 0},
    "Guli":     {"fix": 0, "percent": 0, "plan": 0},
    "Oydinoy":  {"fix": 0, "percent": 0, "plan": 0},
    "Sevinch":  {"fix": 0, "percent": 0, "plan": 0},
    "Sevinch 2":{"fix": 0, "percent": 0, "plan": 0},
    "Dilfuza":  {"fix": 0, "percent": 0, "plan": 0},
}
# Загружаем сохранённые настройки, дополняем дефолтными
_saved = load_settings_from_file()
KPI_SETTINGS = {**DEFAULT_SETTINGS, **_saved}
print(f"KPI настройки загружены: {list(KPI_SETTINGS.keys())}")

def get_db_connection(db_name=None):
    name = db_name or DB_NAME
    conn_str = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=" + DB_SERVER + ";"
        "DATABASE=" + name + ";"
        "UID=" + DB_USER + ";"
        "PWD=" + DB_PASS + ";"
    )
    return pyodbc.connect(conn_str)

def get_search_variants(word):
    variants = set()
    variants.add(word)
    LETTER_REPLACEMENTS = [
        ('Ю', 'У'), ('У', 'Ю'), ('Е', 'Э'), ('Э', 'Е'),
        ('И', 'Ы'), ('Ы', 'И'), ('Ё', 'Е'), ('Е', 'Ё'),
        ('Ц', 'С'), ('С', 'Ц'),
    ]
    if len(word) >= 4: variants.add(word[:-1])
    if len(word) >= 5: variants.add(word[:-2])
    if len(word) >= 4: variants.add(word[1:])
    for old_char, new_char in LETTER_REPLACEMENTS:
        if old_char in word:
            variant = word.replace(old_char, new_char, 1)
            variants.add(variant)
            if len(variant) >= 4: variants.add(variant[:-1])
    return variants

def build_search_query(search, branch, limit):
    search = search.strip().upper()
    branch_filter = "AND R.OTDEL = " + str(branch) if branch else ""
    base_select = """
        SELECT TOP """ + str(limit) + """
            G.ID, G.NAME, G.PRODUCER,
            SUM(R.OST) as total_stock,
            MAX(R.PRICEROZ1) as price,
            R.OTDEL
        FROM RESIDUE R
        JOIN GOOD G ON G.ID = R.GOOD
        WHERE R.OST > 0 AND R.PRICEROZ1 > 0
        {where_clause}
        """ + branch_filter + """
        GROUP BY G.ID, G.NAME, G.PRODUCER, R.OTDEL
        ORDER BY 
            CASE WHEN G.NAME LIKE '""" + search + """%' THEN 0
                 WHEN G.NAME LIKE '%""" + search + """%' THEN 1
                 ELSE 2 END,
            G.NAME
    """
    exact_query = base_select.format(where_clause="AND G.NAME LIKE '%" + search + "%'")
    words = search.split()
    all_variants = set()
    for word in words:
        if len(word) >= 3:
            all_variants.update(get_search_variants(word))
    fuzzy_conditions = ["G.NAME LIKE '%" + v + "%'" for v in all_variants if len(v) >= 3]
    fuzzy_where = "AND (" + " OR ".join(fuzzy_conditions) + ")" if fuzzy_conditions else "AND G.NAME LIKE '%" + search + "%'"
    fuzzy_query = base_select.format(where_clause=fuzzy_where)
    return exact_query, fuzzy_query


# ===== MEDICINES API =====

@app.get("/")
def root():
    return {"status": "M-MED API работает", "version": "4.0"}

@app.get("/branches")
def get_branches():
    return [{"id": k, "name_uz": v["name_uz"], "name_ru": v["name_ru"]} for k, v in BRANCHES.items()]

@app.get("/medicines")
def get_medicines(search: Optional[str] = None, branch: Optional[int] = None, limit: int = 100):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        if search and len(search.strip()) >= 2:
            exact_query, fuzzy_query = build_search_query(search.strip(), branch, limit)
            cursor.execute(exact_query)
            rows = cursor.fetchall()
            if not rows:
                cursor.execute(fuzzy_query)
                rows = cursor.fetchall()
        else:
            branch_filter = "AND R.OTDEL = " + str(branch) if branch else ""
            query = """SELECT TOP """ + str(limit) + """ G.ID, G.NAME, G.PRODUCER, SUM(R.OST), MAX(R.PRICEROZ1), R.OTDEL FROM RESIDUE R JOIN GOOD G ON G.ID = R.GOOD WHERE R.OST > 0 AND R.PRICEROZ1 > 0 """ + branch_filter + """ GROUP BY G.ID, G.NAME, G.PRODUCER, R.OTDEL ORDER BY G.NAME"""
            cursor.execute(query)
            rows = cursor.fetchall()
        conn.close()
        result = []
        for row in rows:
            otdel = row[5]
            branch_info = BRANCHES.get(otdel, {})
            result.append({"id": row[0], "name": row[1], "producer": str(row[2]) if row[2] else "", "stock": float(row[3]) if row[3] else 0, "price": float(row[4]) if row[4] else 0, "branch_id": otdel, "branch_uz": branch_info.get("name_uz", ""), "branch_ru": branch_info.get("name_ru", "")})
        return result
    except Exception as e:
        return {"error": str(e)}

@app.get("/loyalty/{phone}")
def get_loyalty(phone: str):
    phone = phone.replace(" ", "").replace("-", "")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT ID, NAME, NAC, PROC FROM PNAC WHERE NAC = ?", phone)
        row = cursor.fetchone()
        conn.close()
        if row:
            points = int(row[2]) if row[2] else 0
            return {"found": True, "name": row[1] or "", "phone": phone, "points": points, "level": get_level(points), "discount": get_discount(points)}
        return {"found": False}
    except Exception as e:
        return {"found": False, "error": str(e)}

def get_level(p):
    if p >= 5000: return "Platina"
    if p >= 2000: return "Oltin"
    if p >= 500: return "Kumush"
    return "Standart"

def get_discount(p):
    if p >= 5000: return "10%"
    if p >= 2000: return "5%"
    if p >= 500: return "3%"
    return "0%"


# ===== KPI API =====

class LoginData(BaseModel):
    login: str
    password: str

class KpiSettings(BaseModel):
    name: str
    fix: float
    percent: float
    plan: float = 0

@app.post("/kpi/login")
def kpi_login(data: LoginData):
    login = data.login.lower().strip()
    if login == "adm" and data.password == KPI_PASSWORD_ADMIN:
        return {"success": True, "role": "admin", "name": "Администратор"}
    if login in KPI_USERS and data.password == KPI_PASSWORD_STAFF:
        user = KPI_USERS[login]
        return {"success": True, "role": user["role"], "name": user["name"], "branch": user["branch"]}
    return {"success": False, "message": "Неверный логин или пароль"}

@app.get("/kpi/stats")
def get_kpi_stats(period: str = "month", branch: Optional[int] = None, month: Optional[str] = None):
    """Получить статистику продаж по фармацевтам"""
    try:
        today = date.today()
        from datetime import timedelta
        date_to = None
        if month:
            # Конкретный месяц: например "2026-05"
            year, mon = int(month.split('-')[0]), int(month.split('-')[1])
            date_from = month + "-01"
            if mon == 12:
                date_to = str(year+1) + "-01-01"
            else:
                date_to = month[:5] + str(mon+1).zfill(2) + "-01"
        elif period == "day":
            date_from = today.strftime("%Y-%m-%d")
        elif period == "week":
            date_from = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        elif period == "all":
            date_from = "2020-01-01"
        else:
            date_from = today.strftime("%Y-%m-01")

        conn = get_db_connection(DB_GLOBAL)
        cursor = conn.cursor()

        branch_filter = "AND I.OTDEL = " + str(branch) if branch else "AND I.OTDEL IN (3, 4, 6)"

        query = """
            SELECT 
                CASE 
                    WHEN U.NAME = 'Sevinch' AND U.ID = 300000064 THEN 'Sevinch'
                    WHEN U.NAME = 'Sevinch' AND U.ID = 300000065 THEN 'Sevinch 2'
                    ELSE U.NAME 
                END as FARMATSEVT,
                I.OTDEL,
                COUNT(I.ID) as SOTISHLAR,
                SUM(I.SUMMA) as JAMI_SUMMA
            FROM INVOICE I
            LEFT JOIN USERS U ON U.ID = I.USERS
            WHERE CAST(I.DATAENTER as DATE) >= '""" + date_from + """'
              AND ('""" + (date_to or '2099-01-01') + """' = '2099-01-01' OR CAST(I.DATAENTER as DATE) < '""" + (date_to or '2099-01-01') + """')
              AND I.SUMMA > 0
              AND U.NAME NOT LIKE N'КАССА%'
              AND U.NAME NOT LIKE 'KASSA%'
              AND U.NAME != N'АДМИНИСТРАТОР'
              AND U.NAME != 'MANAGER'
              AND U.ID NOT IN (300000055, 200000049, 300000052, 300000049, 150000050)
              """ + branch_filter + """
            GROUP BY 
                CASE 
                    WHEN U.NAME = 'Sevinch' AND U.ID = 300000064 THEN 'Sevinch'
                    WHEN U.NAME = 'Sevinch' AND U.ID = 300000065 THEN 'Sevinch 2'
                    ELSE U.NAME 
                END,
                I.OTDEL
            ORDER BY JAMI_SUMMA DESC
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()

        result = []
        for i, row in enumerate(rows):
            name = row[0] or "Неизвестно"
            otdel = row[1]
            count = row[2]
            summa = float(row[3]) if row[3] else 0
            branch_info = BRANCHES.get(otdel, {})
            settings = KPI_SETTINGS.get(name, {"fix": 0, "percent": 0})
            salary = settings["fix"] + (summa * settings["percent"] / 100)
            plan = settings.get("plan", 0)
            plan_pct = round((summa / plan * 100), 1) if plan > 0 else 0
            result.append({
                "rank": i + 1,
                "name": name,
                "branch_id": otdel,
                "branch_ru": branch_info.get("name_ru", ""),
                "branch_uz": branch_info.get("name_uz", ""),
                "count": count,
                "summa": summa,
                "fix": settings["fix"],
                "percent": settings["percent"],
                "plan": plan,
                "plan_pct": plan_pct,
                "salary": salary,
            })
        return result
    except Exception as e:
        return {"error": str(e)}

@app.post("/kpi/settings")
def update_kpi_settings(data: KpiSettings):
    """Обновить настройки зарплаты фармацевта"""
    KPI_SETTINGS[data.name] = {"fix": data.fix, "percent": data.percent, "plan": data.plan}
    save_settings_to_file(KPI_SETTINGS)
    return {"success": True}

class SalaryRecord(BaseModel):
    month: str  # "2026-06"
    name: str
    summa: float
    fix: float
    percent: float
    salary: float
    plan: float = 0
    plan_pct: float = 0

@app.post("/kpi/history/save")
def save_salary_history(data: SalaryRecord):
    """Сохранить зарплату за месяц"""
    if data.month not in KPI_HISTORY:
        KPI_HISTORY[data.month] = {}
    KPI_HISTORY[data.month][data.name] = {
        "summa": data.summa,
        "fix": data.fix,
        "percent": data.percent,
        "salary": data.salary,
        "plan": data.plan,
        "plan_pct": data.plan_pct,
    }
    save_history(KPI_HISTORY)
    return {"success": True}

@app.get("/kpi/history")
def get_salary_history(name: str = None):
    """Получить историю зарплат"""
    if name:
        result = {}
        for month, records in KPI_HISTORY.items():
            if name in records:
                result[month] = records[name]
        return result
    return KPI_HISTORY

@app.get("/kpi/settings")
def get_all_kpi_settings():
    return KPI_SETTINGS

@app.get("/kpi/chart")
def get_kpi_chart(month: str = None, branch: Optional[int] = None):
    """Продажи по дням месяца для графика"""
    try:
        today = date.today()
        if month:
            date_from = month + "-01"
            year, mon = int(month.split('-')[0]), int(month.split('-')[1])
            if mon == 12:
                date_to = str(year+1) + "-01-01"
            else:
                date_to = month[:5] + str(mon+1).zfill(2) + "-01"
        else:
            date_from = today.strftime("%Y-%m-01")
            date_to = today.strftime("%Y-%m-") + "31"

        branch_filter = "AND I.OTDEL = " + str(branch) if branch else "AND I.OTDEL IN (3, 4, 6)"

        conn = get_db_connection(DB_GLOBAL)
        cursor = conn.cursor()
        query = """
            SELECT 
                CASE 
                    WHEN U.NAME = 'Sevinch' AND U.ID = 300000064 THEN 'Sevinch'
                    WHEN U.NAME = 'Sevinch' AND U.ID = 300000065 THEN 'Sevinch 2'
                    ELSE U.NAME 
                END as FARMATSEVT,
                CAST(I.DATAENTER as DATE) as KUN,
                SUM(I.SUMMA) as SUMMA
            FROM INVOICE I
            LEFT JOIN USERS U ON U.ID = I.USERS
            WHERE CAST(I.DATAENTER as DATE) >= '""" + date_from + """'
              AND CAST(I.DATAENTER as DATE) < '""" + date_to + """'
              AND I.SUMMA > 0
              AND U.NAME NOT LIKE N'КАССА%'
              AND U.NAME NOT LIKE 'KASSA%'
              AND U.NAME != N'АДМИНИСТРАТОР'
              AND U.NAME != 'MANAGER'
              AND U.ID NOT IN (300000055, 200000049, 300000052, 300000049, 150000050)
              """ + branch_filter + """
            GROUP BY 
                CASE 
                    WHEN U.NAME = 'Sevinch' AND U.ID = 300000064 THEN 'Sevinch'
                    WHEN U.NAME = 'Sevinch' AND U.ID = 300000065 THEN 'Sevinch 2'
                    ELSE U.NAME 
                END,
                CAST(I.DATAENTER as DATE)
            ORDER BY KUN, FARMATSEVT
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()

        result = {}
        for row in rows:
            name = row[0] or "Неизвестно"
            day = str(row[1])
            summa = float(row[2]) if row[2] else 0
            if name not in result:
                result[name] = []
            result[name].append({"day": day, "summa": summa})

        return result
    except Exception as e:
        return {"error": str(e)}

@app.get("/kpi/compare")
def get_kpi_compare():
    """Сравнение текущего и прошлого месяца по филиалам и фармацевтам"""
    try:
        today = date.today()
        # Текущий месяц
        cur_from = today.strftime("%Y-%m-01")
        # Прошлый месяц
        if today.month == 1:
            prev_from = str(today.year-1) + "-12-01"
            prev_to = today.strftime("%Y-%m-01")
        else:
            prev_from = today.strftime("%Y-") + str(today.month-1).zfill(2) + "-01"
            prev_to = today.strftime("%Y-%m-01")

        conn = get_db_connection(DB_GLOBAL)
        cursor = conn.cursor()

        def get_stats(date_from, date_to=None):
            date_filter = "CAST(I.DATAENTER as DATE) >= '" + date_from + "'"
            if date_to:
                date_filter += " AND CAST(I.DATAENTER as DATE) < '" + date_to + "'"

            # По филиалам
            cursor.execute("""
                SELECT I.OTDEL, SUM(I.SUMMA) as SUMMA, COUNT(I.ID) as CHEK
                FROM INVOICE I
                WHERE """ + date_filter + """
                  AND I.SUMMA > 0
                  AND I.OTDEL IN (3, 4, 6)
                GROUP BY I.OTDEL
            """)
            branches = {row[0]: {"summa": float(row[1] or 0), "count": row[2]} for row in cursor.fetchall()}

            # По фармацевтам
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN U.NAME = 'Sevinch' AND U.ID = 300000064 THEN 'Sevinch'
                        WHEN U.NAME = 'Sevinch' AND U.ID = 300000065 THEN 'Sevinch 2'
                        ELSE U.NAME 
                    END as FARMATSEVT,
                    I.OTDEL,
                    SUM(I.SUMMA) as SUMMA
                FROM INVOICE I
                LEFT JOIN USERS U ON U.ID = I.USERS
                WHERE """ + date_filter + """
                  AND I.SUMMA > 0
                  AND U.NAME NOT LIKE N'КАССА%'
                  AND U.NAME NOT LIKE 'KASSA%'
                  AND U.NAME != N'АДМИНИСТРАТОР'
                  AND U.NAME != 'MANAGER'
                  AND U.ID NOT IN (300000055, 200000049, 300000052, 300000049, 150000050)
                  AND I.OTDEL IN (3, 4, 6)
                GROUP BY 
                    CASE 
                        WHEN U.NAME = 'Sevinch' AND U.ID = 300000064 THEN 'Sevinch'
                        WHEN U.NAME = 'Sevinch' AND U.ID = 300000065 THEN 'Sevinch 2'
                        ELSE U.NAME 
                    END,
                    I.OTDEL
            """)
            pharmacists = {row[0]: {"summa": float(row[2] or 0), "branch_id": row[1]} for row in cursor.fetchall()}
            return branches, pharmacists

        cur_branches, cur_pharm = get_stats(cur_from)
        prev_branches, prev_pharm = get_stats(prev_from, prev_to)
        conn.close()

        # Формируем результат по филиалам
        branch_compare = []
        for otdel, info in BRANCHES.items():
            cur = cur_branches.get(otdel, {"summa": 0, "count": 0})
            prev = prev_branches.get(otdel, {"summa": 0, "count": 0})
            diff = cur["summa"] - prev["summa"]
            pct = round((diff / prev["summa"] * 100), 1) if prev["summa"] > 0 else 0
            branch_compare.append({
                "branch_id": otdel,
                "branch_ru": info["name_ru"],
                "branch_uz": info["name_uz"],
                "cur_summa": cur["summa"],
                "prev_summa": prev["summa"],
                "diff": diff,
                "pct": pct,
            })

        # Формируем результат по фармацевтам
        all_names = set(list(cur_pharm.keys()) + list(prev_pharm.keys()))
        pharm_compare = []
        for name in all_names:
            cur = cur_pharm.get(name, {"summa": 0, "branch_id": 0})
            prev = prev_pharm.get(name, {"summa": 0, "branch_id": 0})
            diff = cur["summa"] - prev["summa"]
            pct = round((diff / prev["summa"] * 100), 1) if prev["summa"] > 0 else 0
            branch_id = cur.get("branch_id") or prev.get("branch_id")
            branch_info = BRANCHES.get(branch_id, {})
            pharm_compare.append({
                "name": name,
                "branch_id": branch_id,
                "branch_ru": branch_info.get("name_ru", ""),
                "cur_summa": cur["summa"],
                "prev_summa": prev["summa"],
                "diff": diff,
                "pct": pct,
            })
        pharm_compare.sort(key=lambda x: x["cur_summa"], reverse=True)

        cur_month = today.strftime("%Y-%m")
        prev_month = (today.replace(day=1) - __import__('datetime').timedelta(days=1)).strftime("%Y-%m")

        return {
            "cur_month": cur_month,
            "prev_month": prev_month,
            "branches": branch_compare,
            "pharmacists": pharm_compare
        }
    except Exception as e:
        return {"error": str(e)}
