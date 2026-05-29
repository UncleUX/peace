import os
import sys
import django

# Configuration Django
sys.path.append('e:/ELEARNING/crvslearning')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crvslearning.settings')
django.setup()

from django.contrib.auth import get_user_model
from tracking.models import LearnerProgress
from courses.models import Enrollment, Course

def diagnose_cynthia():
    print("🔍 DIAGNOSTIC COMPLET - CYNTHIA.ESSOMBA")
    print("=" * 60)
    
    # Récupérer l'utilisateur
    User = get_user_model()
    try:
        cynthia = User.objects.get(username='cynthia.essomba')
        print(f"✅ Utilisateur: {cynthia.username} (ID: {cynthia.id})")
    except User.DoesNotExist:
        print("❌ Utilisateur non trouvé")
        return
    
    print("\n📊 1. INSCRIPTIONS (Enrollment):")
    enrollments = Enrollment.objects.filter(user=cynthia).select_related('course')
    print(f"   Total: {enrollments.count()}")
    
    for enrollment in enrollments:
        course = enrollment.course
        print(f"   📚 {course.title} (ID: {course.id})")
        print(f"      Inscrit le: {enrollment.enrolled_at}")
    
    print("\n📈 2. PROGRESSIONS (LearnerProgress):")
    progressions = LearnerProgress.objects.filter(user=cynthia).select_related('course')
    print(f"   Total: {progressions.count()}")
    
    for progress in progressions:
        course = progress.course
        print(f"   📚 {course.title} (ID: {course.id})")
        print(f"      Progression: {progress.completion_percentage}%")
        print(f"      Terminé: {progress.is_completed}")
        print(f"      Dernier accès: {progress.last_accessed}")
    
    print("\n🎯 3. PROGRESSIONS NON TERMINÉES:")
    incomplete_progressions = LearnerProgress.objects.filter(
        user=cynthia,
        is_completed=False
    ).select_related('course')
    print(f"   Total: {incomplete_progressions.count()}")
    
    for progress in incomplete_progressions:
        course = progress.course
        print(f"   📚 {course.title} (ID: {course.id})")
        print(f"      Progression: {progress.completion_percentage}%")
        
        # Vérifier l'inscription
        is_enrolled = Enrollment.objects.filter(
            user=cynthia,
            course=course
        ).exists()
        print(f"      Inscrit: {is_enrolled}")
        
        if is_enrolled and 0 < progress.completion_percentage < 100:
            print(f"      ✅ ÉLIGIBLE AUX RAPPELS")
        else:
            print(f"      ❌ NON ÉLIGIBLE (non inscrit ou progression = 0/100)")
    
    print("\n🎯 4. COURS ÉLIGIBLES AUX RAPPELS:")
    eligible_courses = LearnerProgress.objects.filter(
        user=cynthia,
        completion_percentage__gt=0,
        completion_percentage__lt=100
    ).select_related('course')
    print(f"   Total: {eligible_courses.count()}")
    
    for progress in eligible_courses:
        course = progress.course
        print(f"   📚 {course.title} (ID: {course.id})")
        print(f"      Progression: {progress.completion_percentage}%")
        
        # Vérifier l'inscription
        is_enrolled = Enrollment.objects.filter(
            user=cynthia,
            course=course
        ).exists()
        print(f"      Inscrit: {is_enrolled}")
        
        if is_enrolled:
            print(f"      ✅ APPARAÎTRA DANS LES RAPPELS")
        else:
            print(f"      ❌ N'APPARAÎTRA PAS (non inscrit)")
    
    print("\n🔍 5. RÉSUMÉ:")
    print(f"   - Cours totaux dans la base: {Course.objects.count()}")
    print(f"   - Inscriptions de cynthia: {enrollments.count()}")
    print(f"   - Progressions de cynthia: {progressions.count()}")
    print(f"   - Progressions incomplètes: {incomplete_progressions.count()}")
    print(f"   - Progressions éligibles aux rappels: {eligible_courses.count()}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    diagnose_cynthia()
