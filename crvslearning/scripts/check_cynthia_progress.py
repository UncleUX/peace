import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crvslearning.settings')
django.setup()

from django.contrib.auth import get_user_model
from tracking.models import LearnerProgress
from courses.models import Course

def check_cynthia_progress():
    print("🔍 VÉRIFICATION PROGRESSION GLOBALE DE CYNTHIA.ESSOMBA")
    print("=" * 60)
    
    # Récupérer l'utilisateur cynthia.essomba
    User = get_user_model()
    try:
        cynthia = User.objects.get(username='cynthia.essomba')
        print(f"✅ Utilisateur trouvé: {cynthia.username} (ID: {cynthia.id})")
    except User.DoesNotExist:
        print("❌ Utilisateur cynthia.essomba non trouvé")
        return
    
    print("\n📊 PROGRESSION GLOBALE PAR COURS:")
    progressions = LearnerProgress.objects.filter(user=cynthia).select_related('course')
    print(f"   Total progressions: {progressions.count()}")
    
    for progress in progressions:
        course = progress.course
        print(f"\n📚 {course.title} (ID: {course.id})")
        print(f"   Progression: {progress.completion_percentage}%")
        print(f"   Terminé: {progress.is_completed}")
        print(f"   Dernier accès: {progress.last_accessed}")
        print(f"   Date inscription: {progress.enrollment_date}")
        if progress.completion_date:
            print(f"   Date complétion: {progress.completion_date}")
        print(f"   Leçons terminées: {progress.completed_lessons.count()}")
        
        # Vérifier si c'est une progression active (non terminée, > 0%, < 100%)
        is_active_progression = (
            not progress.is_completed and 
            progress.completion_percentage > 0 and 
            progress.completion_percentage < 100
        )
        print(f"   🎯 Progression ACTIVE: {is_active_progression}")
        
        if is_active_progression:
            print(f"   ✅ DEVRAIT APPARAÎTRE DANS LES RAPPELS")
        else:
            print(f"   ❌ NE DEVRAIT PAS APPARAÎTRE (terminée ou progression = 0%)")
    
    print("\n🎯 RÉSUMÉ DES PROGRESSIONS ACTIVES:")
    active_progressions = LearnerProgress.objects.filter(
        user=cynthia,
        is_completed=False,
        completion_percentage__gt=0,
        completion_percentage__lt=100
    ).select_related('course')
    print(f"   Progressions actives: {active_progressions.count()}")
    
    for progress in active_progressions:
        course = progress.course
        print(f"   📚 {course.title}: {progress.completion_percentage}%")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    check_cynthia_progress()
