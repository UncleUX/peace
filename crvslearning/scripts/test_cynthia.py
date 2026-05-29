import os
import sys
sys.path.append('e:/ELEARNING/crvslearning')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crvslearning.settings')
django.setup()

from django.contrib.auth import get_user_model
from tracking.models import LearnerProgress
from courses.models import Enrollment, Course

def test_cynthia():
    print("🔍 TEST COMPLET - CYNTHIA.ESSOMBA")
    print("=" * 60)
    
    # Récupérer l'utilisateur
    User = get_user_model()
    try:
        cynthia = User.objects.get(username='cynthia.essomba')
        print(f"✅ Utilisateur: {cynthia.username} (ID: {cynthia.id})")
    except User.DoesNotExist:
        print("❌ Utilisateur non trouvé")
        return
    
    print("\n📊 TOUTES LES PROGRESSIONS:")
    progressions = LearnerProgress.objects.filter(user=cynthia).select_related('course')
    print(f"   Total: {progressions.count()}")
    
    for progress in progressions:
        course = progress.course
        print(f"\n📚 {course.title}")
        print(f"   ID: {course.id}")
        print(f"   Progression: {progress.completion_percentage}%")
        print(f"   Terminé: {progress.is_completed}")
        print(f"   Leçons terminées: {progress.completed_lessons.count()}")
        
        # Vérifier l'inscription
        is_enrolled = Enrollment.objects.filter(
            user=cynthia,
            course=course
        ).exists()
        print(f"   Inscrit: {is_enrolled}")
        
        # Vérifier si éligible aux rappels
        is_eligible = (
            not progress.is_completed and 
            progress.completion_percentage > 0 and 
            progress.completion_percentage < 100 and
            is_enrolled
        )
        print(f"   Éligible aux rappels: {is_eligible}")
    
    print("\n🎯 PROGRESSIONS ÉLIGIBLES AUX RAPPELS:")
    eligible = LearnerProgress.objects.filter(
        user=cynthia,
        is_completed=False,
        completion_percentage__gt=0,
        completion_percentage__lt=100
    ).select_related('course')
    print(f"   Total: {eligible.count()}")
    
    for progress in eligible:
        course = progress.course
        is_enrolled = Enrollment.objects.filter(
            user=cynthia,
            course=course
        ).exists()
        print(f"   📚 {course.title}: {progress.completion_percentage}% (inscrit: {is_enrolled})")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_cynthia()
