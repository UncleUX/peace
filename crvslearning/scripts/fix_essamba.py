#!/usr/bin/env python
"""
Script simple pour réparer le parcours d'essamba
Version sans configuration Django complexe
"""

import subprocess
import sys

def run_django_command(command):
    """Exécuter une commande Django et retourner le résultat"""
    try:
        result = subprocess.run(
            ['python', 'manage.py', 'shell', '-c', command],
            cwd='crvslearning',
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return "", str(e), 1

def fix_essamba_learning_path():
    """Réparer le parcours d'apprentissage d'essamba"""
    
    print("🔧 Réparation du parcours d'apprentissage pour essamba...")
    
    # Script Django à exécuter
    django_script = '''
from django.contrib.auth import get_user_model
from courses.models import LearningPath, LearningPathTemplate, Enrollment
from certifications.models import Certification

User = get_user_model()

try:
    user = User.objects.get(username='essamba')
    print(f"✅ Utilisateur trouvé: {user.username}")
    print(f"   Structure: {user.get_structure_display()}")
    
    # Créer ou récupérer le LearningPath
    learning_path, created = LearningPath.objects.get_or_create(user=user)
    if created:
        print("✅ LearningPath créé")
    
    # Trouver un template approprié
    template = LearningPathTemplate.objects.filter(
        structure=user.structure, 
        is_active=True
    ).first()
    
    if template:
        print(f"📋 Template trouvé: {template.name} ({template.level})")
        
        # Inscrire aux cours du template
        enrolled_count = 0
        for course in template.courses.all():
            enrollment, created = Enrollment.objects.get_or_create(
                user=user, 
                course=course
            )
            if created:
                enrolled_count += 1
        
        if enrolled_count > 0:
            print(f"✅ Inscrit à {enrolled_count} nouveaux cours")
        
        # Assigner le template
        learning_path.template = template
        if template.courses.exists() and not learning_path.current_course:
            learning_path.current_course = template.courses.first()
        learning_path.save()
        
        print("✅ Template assigné avec succès")
        
        # Statistiques finales
        total_courses = template.courses.count()
        completed_courses = learning_path.completed_courses.filter(
            id__in=template.courses.all()
        ).count()
        
        print(f"📊 Progression: {completed_courses}/{total_courses} cours complétés")
        
        # Vérifier les certifications
        certifications = Certification.objects.filter(user=user)
        print(f"🎓 Certifications existantes: {certifications.count()}")
        
        if completed_courses == total_courses and not certifications.exists():
            print("🎯 Éligible à la certification !")
            # La certification sera générée automatiquement par les signaux
        
    else:
        print("❌ Aucun template trouvé pour cette structure")
        
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
'''
    
    # Exécuter le script
    stdout, stderr, returncode = run_django_command(django_script)
    
    if returncode == 0:
        print("🎉 Script exécuté avec succès !")
        print("Résultat:")
        print(stdout)
    else:
        print("❌ Erreur lors de l'exécution:")
        print(stderr)
    
    return returncode == 0

if __name__ == "__main__":
    success = fix_essamba_learning_path()
    if success:
        print("\n✅ Opération terminée avec succès !")
        print("🔄 Veuillez rafraîchir votre dashboard pour voir les changements.")
    else:
        print("\n❌ Une erreur est survenue.")
        print("💡 Essayez d'exécuter manuellement la commande Django ci-dessus.")
