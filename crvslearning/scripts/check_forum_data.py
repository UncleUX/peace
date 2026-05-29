#!/usr/bin/env python
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crvslearning.settings')
django.setup()

from forum.models import Category, Question
from courses.models import Course, Module, Lesson
from users.models import CustomUser
from django.contrib.auth import get_user_model

User = get_user_model()

def check_data():
    print("=== VÉRIFICATION DES DONNÉES DU FORUM ===\n")
    
    # Vérifier les catégories
    categories = Category.objects.all()
    print(f"📁 Catégories trouvées: {categories.count()}")
    for cat in categories:
        print(f"  - {cat.name} (ID: {cat.id})")
    
    if not categories:
        print("❌ Aucune catégorie trouvée! Création de catégories par défaut...")
        create_default_categories()
    
    # Vérifier les cours
    courses = Course.objects.all()
    print(f"\n📚 Cours trouvés: {courses.count()}")
    for course in courses:
        print(f"  - {course.title} (ID: {course.id})")
    
    # Vérifier les utilisateurs
    users = User.objects.all()
    print(f"\n👥 Utilisateurs trouvés: {users.count()}")
    for user in users[:3]:  # Limiter à 3 pour l'affichage
        print(f"  - {user.username} (ID: {user.id})")
        if hasattr(user, 'courses_enrolled'):
            enrolled = user.courses_enrolled.all()
            print(f"    Cours inscrits: {enrolled.count()}")
            for course in enrolled:
                print(f"      - {course.title}")
    
    # Vérifier les questions
    questions = Question.objects.all()
    print(f"\n❓ Questions trouvées: {questions.count()}")
    for q in questions[:3]:  # Limiter à 3 pour l'affichage
        print(f"  - {q.title} par {q.author.username}")

def create_default_categories():
    """Créer des catégories par défaut si elles n'existent pas"""
    default_categories = [
        {"name": "État Civil", "color": "#007bff", "description": "Questions sur l'état civil"},
        {"name": "Naissance", "color": "#28a745", "description": "Questions concernant les naissances"},
        {"name": "Mariage", "color": "#dc3545", "description": "Questions sur les mariages"},
        {"name": "Décès", "color": "#6c757d", "description": "Questions concernant les décès"},
        {"name": "Documents", "color": "#fd7e14", "description": "Questions sur les documents administratifs"},
        {"name": "Procédures", "color": "#20c997", "description": "Questions sur les procédures administratives"},
    ]
    
    created_count = 0
    for cat_data in default_categories:
        if not Category.objects.filter(name=cat_data["name"]).exists():
            Category.objects.create(**cat_data)
            created_count += 1
            print(f"✅ Catégorie créée: {cat_data['name']}")
    
    print(f"🎉 {created_count} catégories créées avec succès!")

if __name__ == "__main__":
    check_data()
