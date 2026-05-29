from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from courses.models import LearningPath, LearningPathTemplate

class Command(BaseCommand):
    help = 'Assigner automatiquement les templates aux utilisateurs qui n\'en ont pas'

    def handle(self, *args, **options):
        self.stdout.write('🎯 Assignation massive des templates manquants...')
        
        User = get_user_model()
        assigned_count = 0
        error_count = 0
        
        # Parcourir tous les templates actifs
        templates = LearningPathTemplate.objects.filter(is_active=True)
        
        for template in templates:
            self.stdout.write(f"\n📋 Template: {template.name} ({template.get_structure_display()})")
            
            # Trouver tous les utilisateurs de cette structure sans template
            users_without_template = []
            for user in User.objects.filter(structure=template.structure):
                try:
                    lp = LearningPath.objects.get(user=user)
                    if lp.template is None:
                        users_without_template.append(user)
                except LearningPath.DoesNotExist:
                    users_without_template.append(user)
            
            # Assigner le template à tous ces utilisateurs
            for user in users_without_template:
                try:
                    template.assign_to_user(user)
                    assigned_count += 1
                    self.stdout.write(f"  ✅ {user.username} -> {template.name}")
                except Exception as e:
                    error_count += 1
                    self.stdout.write(self.style.ERROR(f"  ❌ Erreur {user.username}: {e}"))
        
        # Résumé
        self.stdout.write(self.style.SUCCESS(f"\n🎉 Assignation terminée!"))
        self.stdout.write(f"✅ {assigned_count} utilisateurs ont reçu un template")
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f"❌ {error_count} erreurs rencontrées"))
        else:
            self.stdout.write(self.style.SUCCESS("🏆 Aucune erreur!"))
