#!/usr/bin/env python
"""
Script pour vérifier si l'utilisateur uptime.sale a un certificat
"""

import subprocess
import sys

def check_uptime_cert():
    """Vérifie si uptime.sale a un certificat"""
    
    print("🔍 Vérification du certificat pour uptime.sale...")
    print("=" * 50)
    
    check_script = '''
import os
import sys

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crvslearning.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()

from django.contrib.auth import get_user_model
from courses.models import LearningPath, CourseCompletion
from certifications.models import Certification

User = get_user_model()

print("📊 VÉRIFICATION UTILISATEUR: uptime.sale")
print("=" * 50)

# 1. Chercher l'utilisateur
try:
    user = User.objects.get(username='uptime.sale')
    print(f"✅ Utilisateur trouvé: {user.username}")
    print(f"📧 Email: {user.email}")
    print(f"🏢 Structure: {user.get_structure_display()}")
    print(f"👤 Nom: {user.get_full_name()}")
    
except User.DoesNotExist:
    print("❌ Utilisateur uptime.sale non trouvé")
    print("🔍 Recherche d'utilisateurs similaires...")
    
    # Chercher des utilisateurs avec 'uptime' dans le nom/email
    similar_users = User.objects.filter(
        username__icontains='uptime'
    ) | User.objects.filter(
        email__icontains='uptime'
    )
    
    if similar_users.exists():
        print("📋 Utilisateurs similaires trouvés:")
        for u in similar_users:
            print(f"   - {u.username} ({u.email})")
    else:
        print("❌ Aucun utilisateur similaire trouvé")
    
    sys.exit(1)

# 2. Vérifier son LearningPath
try:
    lp = LearningPath.objects.get(user=user)
    print(f"\\n📚 PARCOURS D'APPRENTISSAGE")
    print("-" * 30)
    
    if lp.template:
        print(f"🎯 Template: {lp.template.name}")
        print(f"📈 Niveau: {lp.template.get_level_display()}")
        print(f"🏢 Structure: {lp.template.get_structure_display()}")
        
        total_courses = lp.template.courses.count()
        completed = lp.completed_courses.filter(id__in=lp.template.courses.all()).count()
        progress = (completed / total_courses * 100) if total_courses > 0 else 0
        
        print(f"📊 Progression: {progress:.1f}% ({completed}/{total_courses} cours)")
        print(f"🎓 Certification obtenue: {'Oui' if lp.certification_obtained else 'Non'}")
        
        if lp.certification_obtained:
            print(f"📅 Date certification: {lp.certification_date}")
        else:
            print("❌ Pas encore de certification")
            
    else:
        print("❌ Aucun template assigné")
        
except LearningPath.DoesNotExist:
    print("❌ Aucun LearningPath trouvé pour uptime.sale")

# 3. Vérifier ses certifications
print(f"\\n🏆 CERTIFICATIONS")
print("-" * 20)

certifications = Certification.objects.filter(user=user)
print(f"📋 Nombre de certifications: {certifications.count()}")

if certifications.exists():
    for i, cert in enumerate(certifications, 1):
        print(f"\\n🏆 Certification {i}:")
        print(f"   📋 Code: {cert.code}")
        print(f"   📚 Cours: {cert.course.title}")
        print(f"   📊 Niveau: {cert.get_level_display()}")
        print(f"   📅 Date: {cert.issued_at}")
        print(f"   📄 Titre: {cert.title}")
        print(f"   ✅ Valide: {'Oui' if cert.is_valid else 'Non'}")
        print(f"   📎 PDF: {'Oui' if cert.pdf else 'Non'}")
else:
    print("❌ Aucune certification trouvée")

# 4. Vérifier les complétions de cours
print(f"\\n📋 COMPLÉTIONS DE COURS")
print("-" * 25)

completions = CourseCompletion.objects.filter(user=user).order_by('-completed_at')
print(f"📊 Nombre de cours terminés: {completions.count()}")

if completions.exists():
    for i, comp in enumerate(completions[:10], 1):  # Limiter à 10
        print(f"   {i}. {comp.course.title} - {comp.completed_at}")
else:
    print("❌ Aucun cours terminé")

# 5. Statut global
print(f"\\n📊 STATUT GLOBAL")
print("-" * 15)

if certifications.exists():
    print("✅ L'utilisateur uptime.sale a AU MOINS UNE certification")
    print(f"📋 Total: {certifications.count()} certification(s)")
else:
    print("❌ L'utilisateur uptime.sale n'a AUCUNE certification")

if completions.exists():
    print(f"📚 {completions.count()} cours terminés")
else:
    print("❌ Aucun cours terminé")

print(f"\\n🎯 CONCLUSION")
print("-" * 12)
if certifications.exists():
    print("🏆 OUI - uptime.sale a obtenu une certification !")
else:
    print("❌ NON - uptime.sale n'a pas de certification")
'''
    
    try:
        result = subprocess.run(
            ['python3', 'manage.py', 'shell', '-c', check_script],
            cwd='crvslearning',
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print("Résultat de la vérification:")
        print(result.stdout)
        if result.stderr:
            print("Erreurs:")
            print(result.stderr)
            
    except Exception as e:
        print(f"❌ Erreur d'exécution: {e}")

if __name__ == "__main__":
    check_uptime_cert()
