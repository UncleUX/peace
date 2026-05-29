import sqlite3

conn = sqlite3.connect('crvslearning/db.sqlite3')
cursor = conn.cursor()

print("=== Toutes les tables de la base de données ===")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
for table in tables:
    table_name = table[0]
    if 'quiz' in table_name.lower() or 'attempt' in table_name.lower():
        print(f"*** {table_name} ***")
    else:
        print(f"    {table_name}")

conn.close()
