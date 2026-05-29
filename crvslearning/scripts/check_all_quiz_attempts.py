import sqlite3

conn = sqlite3.connect('crvslearning/db.sqlite3')
cursor = conn.cursor()

print("=== TOUS les QuizAttempt dans la base ===")
cursor.execute('SELECT id, quiz_id, user_id, score, is_passed, completed_at FROM courses_quizattempt')
all_attempts = cursor.fetchall()
print(f"Nombre total de QuizAttempt: {len(all_attempts)}")
for row in all_attempts:
    print(f"ID: {row[0]}, Quiz ID: {row[1]}, User ID: {row[2]}, Score: {row[3]}, Passed: {row[4]}, Completed: {row[5]}")

print("\n=== QuizAttempt par utilisateur ===")
cursor.execute('SELECT user_id, COUNT(*) FROM courses_quizattempt GROUP BY user_id')
users_attempts = cursor.fetchall()
for row in users_attempts:
    print(f"User ID: {row[0]}, Nombre de quiz: {row[1]}")

conn.close()
