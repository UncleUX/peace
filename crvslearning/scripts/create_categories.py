from django.core.management.base import BaseCommand
from forum.models import Category

class Command(BaseCommand):
    help = 'Crée les catégories par défaut pour le forum'

    def handle(self, *args, **options):
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
                    'description': f'Questions relatives à {cat_data["name"].lower()}'
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✅ Catégorie créée: {category.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'ℹ️  Catégorie existante: {category.name}'))
        
        self.stdout.write(self.style.SUCCESS(f'\\nNombre final de catégories: {Category.objects.count()}'))
