import sqlite3

conn = sqlite3.connect('crvslearning/db.sqlite3')
cursor = conn.cursor()

print("=== Enrollments ===")
cursor.execute('SELECT id, user_id, course_id FROM courses_enrollment LIMIT 20')
for row in cursor.fetchall():
    print(f"ID: {row[0]}, User ID: {row[1]}, Course ID: {row[2]}")

print("\n=== LessonProgress ===")
cursor.execute('SELECT id, user_id, lesson_id, completed FROM courses_lessonprogress LIMIT 20')
for row in cursor.fetchall():
    print(f"ID: {row[0]}, User ID: {row[1]}, Lesson ID: {row[2]}, Completed: {row[3]}")

print("\n=== CourseCompletion ===")
cursor.execute('SELECT id, user_id, course_id FROM courses_coursecompletion')
for row in cursor.fetchall():
    print(f"ID: {row[0]}, User ID: {row[1]}, Course ID: {row[2]}")

print("\n=== Lessons ===")
cursor.execute('SELECT id, title, module_id FROM courses_lesson LIMIT 10')
for row in cursor.fetchall():
    print(f"ID: {row[0]}, Title: {row[1]}, Module ID: {row[2]}")

conn.close()
