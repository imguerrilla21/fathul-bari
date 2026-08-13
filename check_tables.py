import sqlite3
conn = sqlite3.connect('fathul_bari.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [r[0] for r in cursor.fetchall()]
print(f"Tables found: {tables}")
if "evaluation_runs_v2" in tables:
    cursor.execute("SELECT COUNT(*) FROM evaluation_runs_v2;")
    print(f"Count in evaluation_runs_v2: {cursor.fetchone()[0]}")
else:
    print("evaluation_runs_v2 does NOT exist.")
