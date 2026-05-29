#!/usr/bin/env python
"""
Script de test pour les nouvelles fonctionnalités d'assignation de templates
"""

import subprocess
import sys

def test_template_assignment():
    """Tester les nouvelles fonctionnalités d'assignation"""
    
    print("🧪 Test des nouvelles fonctionnalités d'assignation de templates")
    print("=" * 60)
    
    # Script de test Django
    test_script = '''
from django.contrib.auth import get_user_model
from courses.models import LearningPathTemplate, LearningPath
from django.db import transaction

User = get_user_model()

print("📋 Test 1: Création d'un template avec utilisateurs spécifiques")
print("-" * 50)

try:
    with transaction.atomic():
        # Créer un template pour utilisateurs spécifiques
        template = LearningPathTemplate.objects.create(
            name="Parcours Avancé Spécifique",
            structure="commune",
            level="advanced",
            description="Template avancé pour utilisateurs spécifiques",
            assignment_mode="users_only",
            enable_notifications=True,
            notification_message="🎯 Un parcours avancé spécial a été créé pour vous !"
        )
        
        # Ajouter des utilisateurs spécifiques
        users = User.objects.filter(structure='commune')[:3]
        template.assigned_users.set(users)
        
        print(f"✅ Template '{template.name}' créé")
        print(f"📊 Mode d'assignation: {template.get_assignment_mode_display()}")
        print(f"👥 Utilisateurs assignés: {template.assigned_users.count()}")
        print(f"🔔 Notifications activées: {template.enable_notifications}")
        
        # Tester l'éligibilité
        for user in users:
            is_eligible = template.is_user_eligible(user)
            print(f"   - {user.username}: {'✅ Éligible' if is_eligible else '❌ Non éligible'}")
        
        # Tester l'assignation multiple
        print("\\n📋 Test 2: Assignation multiple")
        print("-" * 30)
        assigned_count = template.assign_to_multiple_users(notify=False)
        print(f"✅ {assigned_count} utilisateurs assignés")
        
        # Vérifier les LearningPaths créés
        learning_paths = LearningPath.objects.filter(template=template)
        print(f"📚 {learning_paths.count()} LearningPaths créés")
        
        for lp in learning_paths:
            print(f"   - {lp.user.username}: {lp.template.name}")
        
        # Tester la notification
        print("\\n📋 Test 3: Notification des utilisateurs")
        print("-" * 35)
        notifications_count = template.notify_assigned_users()
        print(f"📧 {notifications_count} notifications envoyées")
        
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()

print("\\n📋 Test 4: Vérification des modes d'assignation")
print("-" * 45)

# Tester différents modes
templates = LearningPathTemplate.objects.all()
for template in templates:
    users = template.get_recommended_users()
    print(f"\\n🎯 Template: {template.name}")
    print(f"   Mode: {template.get_assignment_mode_display()}")
    print(f"   Structure: {template.get_structure_display()}")
    print(f"   Utilisateurs recommandés: {users.count()}")
    
    # Afficher quelques utilisateurs
    for user in users[:3]:
        print(f"   - {user.username} ({user.get_structure_display()})")

print("\\n✅ Tests terminés !")
'''
    
    # Exécuter le test
    try:
        result = subprocess.run(
            ['python', 'manage.py', 'shell', '-c', test_script],
            cwd='crvslearning',
            capture_output=True,
            text=True,
            timeout=60
        )
        
        print("Résultat des tests:")
        print(result.stdout)
        if result.stderr:
            print("Erreurs:")
            print(result.stderr)
            
    except Exception as e:
        print(f"❌ Erreur d'exécution: {e}")

if __name__ == "__main__":
    test_template_assignment()
