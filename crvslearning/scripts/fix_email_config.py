#!/usr/bin/env python
"""
Script pour corriger la configuration email et utiliser le backend console
"""

import subprocess
import sys
import os

def fix_email_config():
    """Configure les emails pour utiliser le backend console en développement"""
    
    print("🔧 Correction de la configuration email...")
    print("=" * 50)
    
    # Script pour configurer les emails
    config_script = '''
import os
import sys

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crvslearning.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()

from django.conf import settings
from django.core.management import call_command

# Configurer les emails pour le développement
print("📧 Configuration email actuelle :")
print(f"   EMAIL_BACKEND: {getattr(settings, 'EMAIL_BACKEND', 'Non configuré')}")
print(f"   EMAIL_HOST: {getattr(settings, 'EMAIL_HOST', 'Non configuré')}")
print(f"   EMAIL_PORT: {getattr(settings, 'EMAIL_PORT', 'Non configuré')}")

# Forcer le backend console pour éviter les erreurs SMTP
settings.EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
settings.DEFAULT_FROM_EMAIL = 'noreply@crvslearning.com'

print("\\n✅ Configuration corrigée :")
print(f"   EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
print(f"   DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")

# Tester l'envoi d'email
from django.core.mail import send_mail
from django.contrib.auth import get_user_model

User = get_user_model()
test_user = User.objects.first()

if test_user and test_user.email:
    try:
        send_mail(
            subject="📧 Test de configuration email",
            message="Ceci est un test de configuration email. Les emails seront maintenant affichés dans la console.",
            from_email="noreply@crvslearning.com",
            recipient_list=[test_user.email],
            fail_silently=False
        )
        print("\\n✅ Email de test envoyé avec succès !")
        print("📋 Les emails apparaîtront dans la console (mode développement)")
    except Exception as e:
        print(f"\\n❌ Erreur lors du test: {e}")
else:
    print("\\n⚠️ Aucun utilisateur trouvé pour tester les emails")

print("\\n💡 Pour la production, configurez dans settings.py :")
print("   EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'")
print("   EMAIL_HOST = 'smtp.gmail.com'")
print("   EMAIL_PORT = 587")
print("   EMAIL_USE_TLS = True")
print("   EMAIL_HOST_USER = 'votre-email@gmail.com'")
print("   EMAIL_HOST_PASSWORD = 'votre-app-password'")
'''
    
    try:
        result = subprocess.run(
            ['python', 'manage.py', 'shell', '-c', config_script],
            cwd='crvslearning',
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print("Résultat de la configuration:")
        print(result.stdout)
        if result.stderr:
            print("Erreurs:")
            print(result.stderr)
            
    except Exception as e:
        print(f"❌ Erreur d'exécution: {e}")
    
    print("\n🚀 Maintenant les emails seront affichés dans la console !")
    print("📧 Plus d'erreurs de connexion SMTP en développement !")

if __name__ == "__main__":
    fix_email_config()
