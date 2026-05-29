#!/usr/bin/env python
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crvslearning.settings')
django.setup()

from forum.models import Category

print("=== Vérification des catégories ===")
print(f"Nombre total de catégories: {Category.objects.count()}")

categories = Category.objects.all()
if categories:
    for cat in categories:
        print(f"- {cat.name} (ID: {cat.id}, Couleur: {cat.color})")
else:
    print("Aucune catégorie trouvée dans la base de données")
    print("Création de catégories par défaut...")
    
    # Créer quelques catégories par défaut
    default_categories = [
        {"name": "Naissance", "color": "#28a745", "icon": "bi-person-plus"},
        {"name": "Mariage", "color": "#007bff", "icon": "bi-heart"},
        {"name": "Décès", "color": "#6c757d", "icon": "bi-x-circle"},
        {"name": "Jugement Supplétif", "color": "#ffc107", "icon": "bi-gavel"},
        {"name": "SIGEC", "color": "#17a2b8", "icon": "bi-file-text"},
        {"name": "Documents", "color": "#6f42c1", "icon": "bi-file-earmark"},
        {"name": "Procédures", "color": "#e83e8c", "icon": "bi-gear"},
        {"name": "Autre", "color": "#6c757d", "icon": "bi-three-dots"},
    ]
    
    for cat_data in default_categories:
        category, created = Category.objects.get_or_create(
            name=cat_data["name"],
            defaults={
                "color": cat_data["color"],
                "icon": cat_data["icon"],
                "description": f"Questions relatives à {cat_data['name'].lower()}"
            }
        )
        if created:
            print(f"✅ Catégorie créée: {category.name}")
        else:
            print(f"ℹ️  Catégorie existante: {category.name}")

print("\n=== Vérification finale ===")
print(f"Nombre total de catégories: {Category.objects.count()}")
