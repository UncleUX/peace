import sqlite3

conn = sqlite3.connect('crvslearning/db.sqlite3')
cursor = conn.cursor()

print("=== Structure de courses_lesson ===")
cursor.execute('PRAGMA table_info(courses_lesson)')
columns = cursor.fetchall()
for col in columns:
    print(col)

print("\n=== Structure de courses_quiz ===")
cursor.execute('PRAGMA table_info(courses_quiz)')
columns = cursor.fetchall()
for col in columns:
    print(col)

print("\n=== Données courses_lesson ===")
cursor.execute('SELECT id, title FROM courses_lesson LIMIT 5')
lessons = cursor.fetchall()
for row in lessons:
    print(f"ID: {row[0]}, Title: {row[1]}")

print("\n=== Données courses_quiz ===")
cursor.execute('SELECT id, title, lesson_id FROM courses_quiz')
quizzes = cursor.fetchall()
for row in quizzes:
    print(f"ID: {row[0]}, Title: {row[1]}, Lesson ID: {row[2]}")

conn.close()
