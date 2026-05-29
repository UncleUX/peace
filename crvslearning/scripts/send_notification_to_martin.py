#!/usr/bin/env python
"""
Script pour envoyer une notification interne à Martin
"""

import subprocess
import sys

def send_notification_to_martin():
    """Envoie une notification interne à l'utilisateur Martin"""
    
    print("📧 Envoi d'une notification interne à Martin...")
    print("=" * 50)
    
    # Script Django pour créer la notification
    notification_script = '''
from django.contrib.auth import get_user_model
from notifications.models import Notification
from django.urls import reverse

User = get_user_model()

# Rechercher l'utilisateur Martin
try:
    # Essayer plusieurs variations du nom
    martin_variations = [
        'martin',
        'Martin', 
        'martin@example.com',
        'admin'  # au cas où
    ]
    
    martin_user = None
    for variation in martin_variations:
        try:
            if '@' in variation:
                martin_user = User.objects.get(email=variation)
            else:
                martin_user = User.objects.get(username=variation)
            print(f"✅ Utilisateur trouvé: {martin_user.username} ({martin_user.email})")
            break
        except User.DoesNotExist:
            continue
    
    if not martin_user:
        print("❌ Utilisateur Martin non trouvé")
        print("Utilisateurs disponibles:")
        for user in User.objects.all():
            print(f"   - {user.username} ({user.email})")
        sys.exit(1)
    
    # Créer la notification
    notification = Notification.objects.create(
        recipient=martin_user,
        title="🎯 Test de notification",
        message="Ceci est une notification de test pour vérifier que le système fonctionne correctement. Vous pouvez maintenant accéder à votre parcours d'apprentissage.",
        notification_type='learning_path',
        action_url=reverse('courses:learning_path_dashboard')
    )
    
    print(f"✅ Notification envoyée à {martin_user.username}")
    print(f"📋 ID de notification: {notification.id}")
    print(f"📅 Date d'envoi: {notification.created_at}")
    print(f"🔗 URL d'action: {notification.action_url}")
    
    # Vérifier les notifications existantes de Martin
    total_notifications = Notification.objects.filter(recipient=martin_user).count()
    print(f"📊 Total des notifications pour Martin: {total_notifications}")
    
    # Afficher les 5 dernières notifications
    print("\\n📋 Dernières notifications de Martin:")
    recent_notifications = Notification.objects.filter(recipient=martin_user).order_by('-created_at')[:5]
    for notif in recent_notifications:
        print(f"   - {notif.created_at.strftime('%d/%m/%Y %H:%M')} : {notif.title}")
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
'''
    
    # Exécuter le script
    try:
        result = subprocess.run(
            ['python', 'manage.py', 'shell', '-c', notification_script],
            cwd='crvslearning',
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print("Résultat:")
        print(result.stdout)
        if result.stderr:
            print("Erreurs:")
            print(result.stderr)
            
    except Exception as e:
        print(f"❌ Erreur d'exécution: {e}")

if __name__ == "__main__":
    send_notification_to_martin()
