import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crvslearning.settings')
django.setup()

from forum.models import Category
from courses.models import Course
from django.contrib.auth import get_user_model

User = get_user_model()

print("=== VÉRIFICATION DE LA BASE DE DONNÉES ===")
print()

# Vérifier les catégories
print("📂 CATÉGORIES:")
categories = Category.objects.all()
if categories:
    for cat in categories:
        print(f"  ✅ {cat.name} (ID: {cat.id})")
else:
    print("  ❌ Aucune catégorie trouvée")
    print("  🔧 Création des catégories par défaut...")
    categories_data = [
        {'name': 'Naissance', 'color': '#28a745', 'icon': 'bi-person-plus'},
        {'name': 'Mariage', 'color': '#007bff', 'icon': 'bi-heart'},
        {'name': 'Décès', 'color': '#6c757d', 'icon': 'bi-x-circle'},
        {'name': 'Jugement Supplétif', 'color': '#ffc107', 'icon': 'bi-gavel'},
        {'name': 'SIGEC', 'color': '#17a2b8', 'icon': 'bi-file-text'},
        {'name': 'Documents', 'color': '#6f42c1', 'icon': 'bi-file-earmark'},
        {'name': 'Procédures', 'color': '#e83e8c', 'icon': 'bi-gear'},
        {'name': 'Autre', 'color': '#6c757d', 'icon': 'bi-three-dots'},
    ]
    for cat_data in categories_data:
        category, created = Category.objects.get_or_create(
            name=cat_data['name'],
            defaults={
                'color': cat_data['color'],
                'icon': cat_data['icon'],
                'description': f'Questions relatives à {cat_data[\"name\"].lower()}'
            }
        )
        if created:
            print(f"    ✅ Créée: {category.name}")

print(f"  📊 Total: {Category.objects.count()} catégories")
print()

# Vérifier les cours
print("📚 COURS:")
courses = Course.objects.all()
if courses:
    for course in courses:
        print(f"  ✅ {course.title} (ID: {course.id})")
else:
    print("  ❌ Aucun cours trouvé")

print(f"  📊 Total: {Course.objects.count()} cours")
print()

# Vérifier les utilisateurs
print("👥 UTILISATEURS:")
users = User.objects.all()
if users:
    for user in users[:3]:  # Limiter à 3 pour l'affichage
        print(f"  ✅ {user.username} (ID: {user.id})")
        if hasattr(user, 'courses_enrolled'):
            enrolled = user.courses_enrolled.all()
            print(f"    📖 Cours inscrits: {enrolled.count()}")
            for course in enrolled:
                print(f"      - {course.title}")
        else:
            print(f"    ⚠️  Pas d'attribut courses_enrolled")
else:
    print("  ❌ Aucun utilisateur trouvé")

print(f"  📊 Total: {User.objects.count()} utilisateurs")
print()

print("=== FIN DE VÉRIFICATION ===")
