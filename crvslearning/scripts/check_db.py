import sqlite3

conn = sqlite3.connect('crvslearning/db.sqlite3')
cursor = conn.cursor()

print("=== LearnerProgress ===")
cursor.execute('SELECT id, user_id, course_id, completion_percentage, is_completed FROM tracking_learnerprogress')
for row in cursor.fetchall():
    print(f"ID: {row[0]}, User ID: {row[1]}, Course ID: {row[2]}, Progress: {row[3]}%, Completed: {row[4]}")

print("\n=== CourseReminder ===")
cursor.execute('SELECT id, user_id, course_id, progress_percentage, is_active FROM tracking_coursereminder')
for row in cursor.fetchall():
    print(f"ID: {row[0]}, User ID: {row[1]}, Course ID: {row[2]}, Progress: {row[3]}%, Active: {row[4]}")

print("\n=== Courses ===")
cursor.execute('SELECT id, title FROM courses_course')
for row in cursor.fetchall():
    print(f"ID: {row[0]}, Title: {row[1]}")

print("\n=== Users ===")
cursor.execute('SELECT id, username, role FROM users_customuser')
for row in cursor.fetchall():
    print(f"ID: {row[0]}, Username: {row[1]}, Role: {row[2]}")

conn.close()
