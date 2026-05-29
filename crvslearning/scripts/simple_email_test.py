#!/usr/bin/env python
"""
Test simple de la configuration email
"""

import subprocess
import sys

def simple_test():
    """Test simple de la configuration email"""
    
    print("Test simple de la configuration email...")
    
    test_script = '''
from django.core.mail import send_mail
from django.contrib.auth import get_user_model

User = get_user_model()
test_user = User.objects.first()

if test_user:
    print(f"Test avec utilisateur: {test_user.username}")
    
    try:
        send_mail(
            subject="Test email",
            message="Ceci est un test",
            from_email="test@example.com",
            recipient_list=[test_user.email],
            fail_silently=False
        )
        print("Email de test envoye avec succes!")
    except Exception as e:
        print(f"Erreur: {e}")
'''
    
    try:
        result = subprocess.run(
            ['python3', 'manage.py', 'shell', '-c', test_script],
            cwd='crvslearning',
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print("Resultat:")
        print(result.stdout)
        if result.stderr:
            print("Erreurs:")
            print(result.stderr)
            
    except Exception as e:
        print(f"Erreur execution: {e}")

if __name__ == "__main__":
    simple_test()
