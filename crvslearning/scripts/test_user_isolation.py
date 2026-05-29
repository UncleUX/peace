#!/usr/bin/env python

import os
import sys

# Ajouter le chemin du projet
sys.path.append('e:/ELEARNING/crvslearning')

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crvslearning.settings')

import django
django.setup()

from django.contrib.auth.models import User
from tracking.models import CourseReminder
from django.db.models import Count

def test_user_isolation():
    print("🔍 TEST D'ISOLATION DES UTILISATEURS")
    print("=" * 60)
    
    try:
        # 1. Lister tous les utilisateurs avec des rappels
        users_with_reminders = User.objects.filter(course_reminders__isnull=False).distinct()
        print(f"👥 Utilisateurs avec des rappels: {users_with_reminders.count()}")
        
        for user in users_with_reminders:
            print(f"\n👤 {user.username} (ID: {user.id})")
            
            # 2. Vérifier les rappels de cet utilisateur
            reminders = CourseReminder.objects.filter(user=user)
            print(f"   📚 Rappels: {reminders.count()}")
            
            for reminder in reminders:
                print(f"      • {reminder.course.title} (ID: {reminder.course.id}) - {reminder.progress_percentage}%")
        
        # 3. Vérifier s'il y a des rappels sans utilisateur valide
        orphaned_reminders = CourseReminder.objects.filter(user__isnull=True)
        if orphaned_reminders.exists():
            print(f"\n⚠️ RAPPELS ORPHELINS: {orphaned_reminders.count()}")
            for reminder in orphaned_reminders:
                print(f"   • Course: {reminder.course.title} - User: NULL")
        
        # 4. Vérifier les doublons potentiels
        duplicate_reminders = CourseReminder.objects.values('user', 'course').annotate(count=models.Count('id')).filter(count__gt=1)
        if duplicate_reminders.exists():
            print(f"\n⚠️ RAPPELS EN DOUBLE: {duplicate_reminders.count()}")
            for dup in duplicate_reminders:
                print(f"   • User {dup['user']} - Course {dup['course']}: {dup['count']} rappels")
        
        print(f"\n✅ Test d'isolation terminé")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_user_isolation()
