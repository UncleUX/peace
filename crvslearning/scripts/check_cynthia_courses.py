#!/usr/bin/env python
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crvslearning.settings')
django.setup()

from django.contrib.auth import get_user_model
from tracking.models import LearnerProgress
from courses.models import Enrollment, Course

def check_cynthia_courses():
    print("🔍 VÉRIFICATION COMPLÈTE DES COURS DE CYNTHIA.ESSOMBA")
    print("=" * 60)
    
    # Récupérer l'utilisateur cynthia.essomba
    User = get_user_model()
    try:
        cynthia = User.objects.get(username='cynthia.essomba')
        print(f"✅ Utilisateur trouvé: {cynthia.username} (ID: {cynthia.id})")
    except User.DoesNotExist:
        print("❌ Utilisateur cynthia.essomba non trouvé")
        return
    
    print("\n📊 1. INSCRIPTIONS (Enrollment):")
    enrollments = Enrollment.objects.filter(user=cynthia).select_related('course')
    print(f"   Total inscriptions: {enrollments.count()}")
    
    for enrollment in enrollments:
        course = enrollment.course
        print(f"   📚 {course.title} (ID: {course.id})")
        print(f"      Inscrit le: {enrollment.enrolled_at}")
    
    print("\n📈 2. PROGRESSIONS (LearnerProgress):")
    progressions = LearnerProgress.objects.filter(user=cynthia).select_related('course')
    print(f"   Total progressions: {progressions.count()}")
    
    for progress in progressions:
        course = progress.course
        print(f"   📚 {course.title} (ID: {course.id})")
        print(f"      Progression: {progress.completion_percentage}%")
        print(f"      Terminé: {progress.is_completed}")
        print(f"      Dernier accès: {progress.last_accessed}")
        print(f"      Date inscription: {progress.enrollment_date}")
        if progress.completion_date:
            print(f"      Date complétion: {progress.completion_date}")
    
    print("\n🎯 3. COURS ÉLIGIBLES AUX RAPPELS:")
    eligible_progressions = LearnerProgress.objects.filter(
        user=cynthia,
        completion_percentage__gt=0,
        completion_percentage__lt=100
    ).select_related('course')
    print(f"   Progressions éligibles: {eligible_progressions.count()}")
    
    for progress in eligible_progressions:
        course = progress.course
        print(f"   📚 {course.title} (ID: {course.id})")
        print(f"      Progression: {progress.completion_percentage}%")
        
        # Vérifier si inscrit
        is_enrolled = Enrollment.objects.filter(
            user=cynthia,
            course=course
        ).exists()
        print(f"      Inscrit: {is_enrolled}")
        
        if is_enrolled:
            print(f"      ✅ DEVRAIT APPARAÎTRE DANS LES RAPPELS")
        else:
            print(f"      ❌ NE SERA PAS DANS LES RAPPELS (non inscrit)")
    
    print("\n🔍 4. DIAGNOSTIC:")
    print(f"   - Nombre total de cours: {Course.objects.count()}")
    print(f"   - Nombre d'inscriptions: {enrollments.count()}")
    print(f"   - Nombre de progressions: {progressions.count()}")
    print(f"   - Progressions éligibles aux rappels: {eligible_progressions.count()}")
    
    if eligible_progressions.count() == 0:
        print("\n❌ PROBLÈME IDENTIFIÉ:")
        print("   Aucune progression éligible aux rappels trouvée")
        print("   Causes possibles:")
        print("   1. Aucune progression avec 0% < progression < 100%")
        print("   2. Toutes les progressions sont à 0% ou 100%")
        print("   3. Problème de cohérence entre Enrollment et LearnerProgress")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    check_cynthia_courses()
