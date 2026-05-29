#!/usr/bin/env python
"""
Script pour envoyer une notification à Martin en une seule commande
"""

import subprocess
import sys
import os

def main():
    """Exécute tout en une seule commande"""
    
    print("📧 Envoi de notification à Martin...")
    print("=" * 50)
    
    # Script Django complet
    django_script = '''
import os
import sys
import django

# Configuration Django avec résolution des conflits
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crvslearning.settings')

# Ajouter les chemins dans le bon ordre pour éviter les conflits
current_dir = os.path.dirname(os.path.abspath(__file__))
crvslearning_dir = os.path.join(current_dir, 'crvslearning')

sys.path.insert(0, current_dir)
sys.path.insert(0, crvslearning_dir)

# Désactiver temporairement l'application documentation en conflit
if 'documentation' in sys.modules:
    del sys.modules['documentation']

django.setup()

from django.contrib.auth import get_user_model
from notifications.models import Notification
from django.urls import reverse

# Chercher Martin
User = get_user_model()
martin = None

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
        sys.exit(1)

# Créer la notification
notification = Notification.objects.create(
    user=martin,
    message="🎯 Test de notification: Ceci est une notification de test pour vérifier que le système fonctionne correctement. Vous pouvez maintenant accéder à votre parcours d'apprentissage.",
    url='/courses/learning-path/'
)

print(f"✅ Notification envoyée avec succès !")
print(f"📋 ID: {notification.id}")
print(f"📅 Date: {notification.created_at}")
print(f"🔗 URL: {notification.url}")
print(f"👤 Destinataire: {martin.username}")
'''
    
    # Créer un fichier temporaire avec le script
    temp_script_path = os.path.join('crvslearning', 'temp_notify_martin.py')
    
    try:
        with open(temp_script_path, 'w', encoding='utf-8') as f:
            f.write(django_script)
        
        # Exécuter le script
        print("🔧 Exécution du script Django...")
        result = subprocess.run(
            ['python', 'temp_notify_martin.py'],
            cwd='crvslearning',
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print(result.stdout)
        if result.stderr:
            print("Erreurs:")
            print(result.stderr)
        
        # Nettoyer le fichier temporaire
        try:
            os.remove(temp_script_path)
        except:
            pass
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    main()
