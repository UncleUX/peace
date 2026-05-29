import os
import sys
import django

# Ajouter le chemin du projet
sys.path.insert(0, 'e:/ELEARNING/crvslearning')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crvslearning.settings')
django.setup()

from tracking.models import LearnerProgress, CourseReminder
from courses.models import Enrollment, Course
from users.models import CustomUser

print("=== LearnerProgress ===")
learner_progress = LearnerProgress.objects.all()
print(f"Total LearnerProgress: {learner_progress.count()}")
for lp in learner_progress:
    print(f"{lp.user.username} - {lp.course.title} - {lp.completion_percentage}%")

print("\n=== CourseReminder ===")
reminders = CourseReminder.objects.all()
print(f"Total CourseReminder: {reminders.count()}")
for r in reminders:
    print(f"{r.user.username} - {r.course.title} - {r.progress_percentage}% - active: {r.is_active}")

print("\n=== Enrollments ===")
enrollments = Enrollment.objects.all()
print(f"Total Enrollments: {enrollments.count()}")
for e in enrollments[:10]:
    print(f"{e.user.username} - {e.course.title}")

print("\n=== Users ===")
users = CustomUser.objects.filter(role='learner')
print(f"Total Learners: {users.count()}")
for u in users[:10]:
    print(f"{u.username} - {u.get_full_name()}")
