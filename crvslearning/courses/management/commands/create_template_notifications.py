from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from courses.models import LearningPathTemplate

class Command(BaseCommand):
    help = 'Crée des templates de parcours et notifie les utilisateurs concernés'

    def add_arguments(self, parser):
        parser.add_argument('--template-name', type=str, help='Nom du template à créer')
        parser.add_argument('--structure', type=str, help='Structure cible')
        parser.add_argument('--level', type=str, help='Niveau (beginner/intermediate/advanced)')
        parser.add_argument('--notify', action='store_true', help='Envoyer les notifications')
        parser.add_argument('--assign', action='store_true', help='Assigner automatiquement aux utilisateurs')

    def handle(self, *args, **options):
        User = get_user_model()
        
        if options.get('template_name'):
            # Créer un nouveau template
            template = LearningPathTemplate.objects.create(
                name=options['template_name'],
                structure=options.get('structure', 'commune'),
                level=options.get('level', 'beginner'),
                description=f"Template {options.get('template_name')} pour {options.get('structure', 'commune')}",
                enable_notifications=True
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'Template "{template.name}" créé avec succès')
            )
            
            if options.get('assign'):
                assigned_count = template.assign_to_multiple_users(notify=options.get('notify', False))
                self.stdout.write(
                    self.style.SUCCESS(f'{assigned_count} utilisateurs assignés')
                )
            
            if options.get('notify'):
                notifications_count = template.notify_assigned_users()
                self.stdout.write(
                    self.style.SUCCESS(f'{notifications_count} notifications envoyées')
                )
        else:
            # Lister les templates existants et leurs utilisateurs
            self.stdout.write(self.style.SUCCESS('Templates de parcours existants:'))
            
            for template in LearningPathTemplate.objects.all():
                users = template.get_recommended_users()
                self.stdout.write(f'\n📋 {template.name}')
                self.stdout.write(f'   Structure: {template.get_structure_display()}')
                self.stdout.write(f'   Niveau: {template.get_level_display()}')
                self.stdout.write(f'   Mode: {template.get_assignment_mode_display()}')
                self.stdout.write(f'   Utilisateurs concernés: {users.count()}')
                
                if template.enable_notifications:
                    self.stdout.write(f'   ✅ Notifications activées')
                else:
                    self.stdout.write(f'   ❌ Notifications désactivées')
