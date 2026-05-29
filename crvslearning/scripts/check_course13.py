import sqlite3

conn = sqlite3.connect('crvslearning/db.sqlite3')
cursor = conn.cursor()

course_id = 13  # TENUE DES REGISTRES
user_id = 38  # cynthia.essomba

print(f"=== Données pour le cours ID {course_id} ===")

print("\n=== Modules du cours ===")
cursor.execute('SELECT id, title, course_id FROM courses_module WHERE course_id = ?', (course_id,))
modules = cursor.fetchall()
print(f"Nombre de modules: {len(modules)}")
for row in modules:
    print(f"ID: {row[0]}, Title: {row[1]}, Course ID: {row[2]}")

print("\n=== Leçons du cours ===")
cursor.execute('''
    SELECT l.id, l.title, l.module_id, m.course_id 
    FROM courses_lesson l 
    JOIN courses_module m ON l.module_id = m.id 
    WHERE m.course_id = ?
''', (course_id,))
lessons = cursor.fetchall()
print(f"Nombre de leçons: {len(lessons)}")
for row in lessons:
    print(f"ID: {row[0]}, Title: {row[1]}, Module ID: {row[2]}")

print(f"\n=== Leçons complétées par cynthia.essomba pour le cours {course_id} ===")
cursor.execute('''
    SELECT lp.id, lp.lesson_id, lp.is_completed, l.title 
    FROM courses_lessonprogress lp 
    JOIN courses_lesson l ON lp.lesson_id = l.id 
    JOIN courses_module m ON l.module_id = m.id 
    WHERE lp.user_id = ? AND m.course_id = ?
''', (user_id, course_id))
user_lessons = cursor.fetchall()
print(f"Nombre de leçons complétées: {len(user_lessons)}")
for row in user_lessons:
    print(f"ID: {row[0]}, Lesson ID: {row[1]}, Completed: {row[2]}, Title: {row[3]}")

conn.close()
