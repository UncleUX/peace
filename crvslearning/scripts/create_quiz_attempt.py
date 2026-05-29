import sqlite3
from datetime import datetime

conn = sqlite3.connect('crvslearning/db.sqlite3')
cursor = conn.cursor()

user_id = 38  # cynthia.essomba
quiz_id = 1  # GENERALITES

# Créer un QuizAttempt avec score 100%
now = datetime.now().isoformat()
cursor.execute('''
    INSERT INTO courses_quizattempt (quiz_id, user_id, score, is_passed, started_at, completed_at)
    VALUES (?, ?, ?, ?, ?, ?)
''', (quiz_id, user_id, 100, 1, now, now))

conn.commit()

print(f"QuizAttempt créé pour l'utilisateur {user_id} avec score 100%")

# Vérifier
cursor.execute('SELECT * FROM courses_quizattempt WHERE user_id = ?', (user_id,))
result = cursor.fetchall()
print(f"QuizAttempt pour l'utilisateur: {result}")

conn.close()
