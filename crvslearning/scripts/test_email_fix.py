#!/usr/bin/env python
"""
Test de la configuration email après correction
"""

import subprocess
import sys

def test_email_config():
    """Test la configuration email corrigée"""
    
    print("📧 Test de la configuration email...")
    print("=" * 50)
    
    test_script = '''
import os
import sys

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crvslearning.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()

from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth import get_user_model

print("📧 Configuration email actuelle :")
print(f"   EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
print(f"   DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
print(f"   DEBUG: {settings.DEBUG}")

# Tester l'envoi d'email
User = get_user_model()
test_user = User.objects.first()

if test_user:
    print(f"\\n👤 Utilisateur de test: {test_user.username} ({test_user.email})")
    
    try:
        # Envoyer un email de test
        send_mail(
            subject="✅ Configuration email corrigée",
            message="Test réussi ! Les emails sont maintenant configurés pour le développement.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[test_user.email],
            fail_silently=False
        )
        print("\\n✅ Email de test envoyé avec succès !")
        print("📋 Les emails apparaîtront dans la console ci-dessus")
        print("🚀 Plus d'erreurs SMTP en développement !")
        
    except Exception as e:
        print(f"\\n❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
else:
    print("\\n⚠️ Aucun utilisateur trouvé pour tester")
'''
    
    try:
        result = subprocess.run(
            ['python', 'manage.py', 'shell', '-c', test_script],
            cwd='crvslearning',
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print("Résultat du test:")
        print(result.stdout)
        if result.stderr:
            print("Erreurs:")
            print(result.stderr)
            
    except Exception as e:
        print(f"❌ Erreur d'exécution: {e}")

if __name__ == "__main__":
    test_email_config()
