import os
import sys
import django

# Ajouter le chemin du projet
sys.path.insert(0, 'e:/ELEARNING/crvslearning')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crvslearning.settings')
django.setup()

from django.contrib.auth import get_user_model
from courses.models import Enrollment, LessonProgress, CourseCompletion
from courses.models import Course

CustomUser = get_user_model()

# Tester avec un utilisateur
user = CustomUser.objects.filter(role='learner').first()
print(f"Test avec utilisateur: {user.username} (ID: {user.id})")

# Récupérer les inscriptions
enrollments = Enrollment.objects.filter(user=user).select_related('course')
print(f"Inscriptions trouvées: {enrollments.count()}")

for enrollment in enrollments:
    course = enrollment.course
    print(f"\nCours: {course.title} (ID: {course.id})")
    
    # Vérifier si complété
    is_completed = CourseCompletion.objects.filter(user=user, course=course).exists()
    print(f"  Complété: {is_completed}")
    
    # Calculer la progression
    total_lessons = course.get_total_lessons()
    print(f"  Total leçons: {total_lessons}")
    
    completed_lessons = LessonProgress.objects.filter(
        user=user,
        lesson__module__course=course,
        completed=True
    ).count()
    print(f"  Leçons complétées: {completed_lessons}")
    
    if total_lessons > 0:
        progress = (completed_lessons / total_lessons) * 100
        print(f"  Progression: {progress:.1f}%")
