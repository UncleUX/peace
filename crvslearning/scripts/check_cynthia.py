import sqlite3

conn = sqlite3.connect('crvslearning/db.sqlite3')
cursor = conn.cursor()

user_id = 38  # cynthia.essomba

print(f"=== Données pour l'utilisateur ID {user_id} (cynthia.essomba) ===")

print("\n=== Enrollments ===")
cursor.execute('SELECT id, user_id, course_id FROM courses_enrollment WHERE user_id = ?', (user_id,))
enrollments = cursor.fetchall()
print(f"Nombre d'inscriptions: {len(enrollments)}")
for row in enrollments:
    print(f"ID: {row[0]}, User ID: {row[1]}, Course ID: {row[2]}")

print("\n=== LessonProgress ===")
cursor.execute('SELECT id, user_id, lesson_id, is_completed FROM courses_lessonprogress WHERE user_id = ?', (user_id,))
lesson_progress = cursor.fetchall()
print(f"Nombre de leçons progress: {len(lesson_progress)}")
for row in lesson_progress:
    print(f"ID: {row[0]}, User ID: {row[1]}, Lesson ID: {row[2]}, Completed: {row[3]}")

print("\n=== CourseCompletion ===")
cursor.execute('SELECT id, user_id, course_id FROM courses_coursecompletion WHERE user_id = ?', (user_id,))
completions = cursor.fetchall()
print(f"Nombre de cours complétés: {len(completions)}")
for row in completions:
    print(f"ID: {row[0]}, User ID: {row[1]}, Course ID: {row[2]}")

print("\n=== Cours disponibles ===")
cursor.execute('SELECT id, title FROM courses_course')
courses = cursor.fetchall()
print(f"Nombre total de cours: {len(courses)}")
for row in courses:
    print(f"ID: {row[0]}, Title: {row[1]}")

conn.close()
