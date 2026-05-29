#!/usr/bin/env python
"""
Script complet pour configurer le système de templates en une seule commande
"""

import subprocess
import sys
import os

def run_command(cmd, description):
    """Exécute une commande et affiche le résultat"""
    print(f"\n🔧 {description}...")
    print(f"Commande: {cmd}")
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd='crvslearning',
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print(f"✅ {description} - Succès")
            if result.stdout:
                print(result.stdout)
        else:
            print(f"❌ {description} - Erreur")
            if result.stderr:
                print(result.stderr)
                
    except Exception as e:
        print(f"❌ {description} - Exception: {e}")

def main():
    """Configuration complète du système de templates"""
    
    print("🚀 Configuration complète du système de templates d'apprentissage")
    print("=" * 60)
    
    # Étape 1: Créer les migrations
    run_command(
        "python manage.py makemigrations courses",
        "Création des migrations pour les nouveaux champs"
    )
    
    # Étape 2: Appliquer les migrations
    run_command(
        "python manage.py migrate", 
        "Application des migrations à la base de données"
    )
    
    # Étape 3: Configurer les emails
    print("\n🔧 Configuration des emails...")
    print("📧 Configuration email par défaut (mode développement):")
    print("   - Backend: Console (emails affichés dans la console)")
    print("   - From: noreply@crvslearning.com")
    print("   - Site: CRVS Learning - Développement")
    print("\n💡 Pour la production, modifiez settings.py avec:")
    print("   EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'")
    print("   EMAIL_HOST = 'smtp.gmail.com'")
    print("   EMAIL_PORT = 587")
    print("   EMAIL_USE_TLS = True")
    print("   EMAIL_HOST_USER = 'votre-email@gmail.com'")
    print("   EMAIL_HOST_PASSWORD = 'votre-app-password'")
    
    # Étape 4: Créer un superutilisateur si nécessaire
    create_superuser = '''
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser(
        username="admin",
        email="admin@example.com", 
        password="admin123",
        first_name="Admin",
        last_name="System"
    )
    print("✅ Superutilisateur créé: admin/admin123")
else:
    print("✅ Superutilisateur existe déjà")
'''
    
    print("\n🔧 Vérification du superutilisateur...")
    try:
        result = subprocess.run(
            ['python', 'manage.py', 'shell', '-c', create_superuser],
            cwd='crvslearning',
            capture_output=True,
            text=True,
            timeout=30
        )
        print(result.stdout)
    except Exception as e:
        print(f"❌ Erreur création superutilisateur: {e}")
    
    # Étape 5: Démarrer le serveur
    print("\n🌐 Démarrage du serveur de développement...")
    print("📍 URL: http://127.0.0.1:8000")
    print("👤 Admin: http://127.0.0.1:8000/admin/")
    print("🔐 Identifiants: admin / admin123")
    print("📧 Les emails seront affichés dans la console (mode développement)")
    print("\n⏹️  Arrêter avec: Ctrl+C")
    
    try:
        subprocess.run(
            "python manage.py runserver",
            shell=True,
            cwd='crvslearning'
        )
    except KeyboardInterrupt:
        print("\n🛑 Serveur arrêté")

if __name__ == "__main__":
    main()
