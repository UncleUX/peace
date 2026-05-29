#!/usr/bin/env python
"""
Script simple pour notifier Martin
"""

import os
import sys

# Ajouter le chemin Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'crvslearning'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crvslearning.settings')

import django
django.setup()

from django.contrib.auth import get_user_model
from notifications.models import Notification
from django.urls import reverse

def main():
    print("📧 Envoi de notification à Martin...")
    
    User = get_user_model()
    
    # Chercher Martin
    try:
        martin = User.objects.get(username='martin')
        print(f"✅ Martin trouvé: {martin.username} ({martin.email})")
    except User.DoesNotExist:
        try:
            martin = User.objects.get(email__icontains='martin')
            print(f"✅ Martin trouvé par email: {martin.username} ({martin.email})")
        except User.DoesNotExist:
            print("❌ Martin non trouvé")
            print("Utilisateurs disponibles:")
            for user in User.objects.all()[:10]:
                print(f"   - {user.username} ({user.email})")
            return
    
    # Créer la notification
    notification = Notification.objects.create(
        user=martin,
        message="🎯 Test de notification: Ceci est une notification de test pour vérifier que le système fonctionne correctement.",
        url='/courses/learning-path/'
    )
    
    print(f"✅ Notification envoyée !")
    print(f"📋 ID: {notification.id}")
    print(f"📅 Date: {notification.created_at}")
    print(f"🔗 URL: {notification.url}")

if __name__ == "__main__":
    main()
