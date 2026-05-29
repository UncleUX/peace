import sqlite3

conn = sqlite3.connect('crvslearning/db.sqlite3')
cursor = conn.cursor()

user_id = 38  # cynthia.essomba

print(f"=== QuizAttempt pour l'utilisateur ID {user_id} ===")
cursor.execute('SELECT id, quiz_id, user_id, score, is_passed, completed_at FROM courses_quizattempt WHERE user_id = ?', (user_id,))
quiz_attempts = cursor.fetchall()
print(f"Nombre de quiz attempts: {len(quiz_attempts)}")
for row in quiz_attempts:
    print(f"ID: {row[0]}, Quiz ID: {row[1]}, User ID: {row[2]}, Score: {row[3]}, Passed: {row[4]}, Completed: {row[5]}")

print(f"\n=== Quiz dans la base ===")
cursor.execute('SELECT id, title FROM courses_quiz LIMIT 10')
quizzes = cursor.fetchall()
print(f"Nombre de quiz: {len(quizzes)}")
for row in quizzes:
    print(f"ID: {row[0]}, Title: {row[1]}")

print(f"\n=== Leçons avec quiz ===")
cursor.execute('SELECT id, title, quiz_id FROM courses_lesson WHERE quiz_id IS NOT NULL LIMIT 10')
lessons = cursor.fetchall()
print(f"Nombre de leçons avec quiz: {len(lessons)}")
for row in lessons:
    print(f"ID: {row[0]}, Title: {row[1]}, Quiz ID: {row[2]}")

print(f"\n=== Modules ===")
cursor.execute('SELECT id, title, course_id FROM courses_module LIMIT 10')
modules = cursor.fetchall()
print(f"Nombre de modules: {len(modules)}")
for row in modules:
    print(f"ID: {row[0]}, Title: {row[1]}, Course ID: {row[2]}")

conn.close()
