import sqlite3

conn = sqlite3.connect('crvslearning/db.sqlite3')
cursor = conn.cursor()

user_id = 38  # cynthia.essomba

print("=== evaluations_attempt ===")
cursor.execute('SELECT * FROM evaluations_attempt WHERE user_id = ?', (user_id,))
eval_attempts = cursor.fetchall()
print(f"Nombre d'evaluations_attempt: {len(eval_attempts)}")
for row in eval_attempts:
    print(row)

print("\n=== exercices_userexerciseattempt ===")
cursor.execute('SELECT * FROM exercices_userexerciseattempt WHERE user_id = ?', (user_id,))
exercise_attempts = cursor.fetchall()
print(f"Nombre d'exercices_userexerciseattempt: {len(exercise_attempts)}")
for row in exercise_attempts:
    print(row)

print("\n=== Structure evaluations_attempt ===")
cursor.execute('PRAGMA table_info(evaluations_attempt)')
columns = cursor.fetchall()
for col in columns:
    print(col)

print("\n=== Structure exercices_userexerciseattempt ===")
cursor.execute('PRAGMA table_info(exercices_userexerciseattempt)')
columns = cursor.fetchall()
for col in columns:
    print(col)

conn.close()
