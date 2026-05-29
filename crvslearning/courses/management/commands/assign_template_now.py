"""
Commande urgente pour assigner un template à l'utilisateur
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from courses.models import LearningPathTemplate

User = get_user_model()


class Command(BaseCommand):
    help = 'Assigner immédiatement un template à essamba.essamba'

    def handle(self, *args, **options):
        self.stdout.write("🚀 ASSIGNATION IMMÉDIATE DU TEMPLATE")
        self.stdout.write("=" * 50)
        
        try:
            # Récupérer l'utilisateur
            user = User.objects.get(username='essamba.essamba')
            self.stdout.write(f"👤 Utilisateur: {user.username}")
            
            # Récupérer le template Expert Commune (ID 4)
            template = LearningPathTemplate.objects.get(id=4)
            self.stdout.write(f"📋 Template: {template.name}")
            
            # Assigner le template
            learning_path = template.assign_to_user(user)
            self.stdout.write(f"✅ Template assigné avec succès")
            
            # Afficher les détails
            self.stdout.write(f"📚 Cours du parcours: {template.courses.count()}")
            self.stdout.write(f"📊 LearningPath ID: {learning_path.id}")
            self.stdout.write(f"🎯 Cours actuel: {learning_path.current_course}")
            
            # Vérifier que les cours sont bien associés
            enrolled_courses = user.enrollment_set.filter(course__in=template.courses.all()).count()
            self.stdout.write(f"📈 Cours où l'utilisateur est inscrit: {enrolled_courses}")
            
            # Synchroniser les cours complétés
            completed_count = 0
            for completion in user.coursecompletion_set.all():
                if completion.course in template.courses.all():
                    learning_path.completed_courses.add(completion.course)
                    completed_count += 1
            
            self.stdout.write(f"✅ Cours complétés synchronisés: {completed_count}")
            
            # Mettre à jour la progression
            total_courses = template.courses.count()
            if total_courses > 0:
                progress_percentage = (completed_count / total_courses) * 100
                learning_path.certification_progress = progress_percentage
                learning_path.save()
                self.stdout.write(f"📊 Progression mise à jour: {progress_percentage:.1f}%")
            
            self.stdout.write("=" * 50)
            self.stdout.write(self.style.SUCCESS("🎓 TEMPLATE ASSIGNÉ AVEC SUCCÈS"))
            self.stdout.write(f"   • Utilisateur: {user.username}")
            self.stdout.write(f"   • Template: {template.name}")
            self.stdout.write(f"   • Cours: {template.courses.count()}")
            self.stdout.write(f"   • Progression: {learning_path.certification_progress}%")
            self.stdout.write("")
            self.stdout.write("🚀 L'utilisateur peut maintenant:")
            self.stdout.write("   1. Voir son parcours dans le dashboard")
            self.stdout.write("   2. Continuer sa progression")
            self.stdout.write("   3. Atteindre 95% pour la certification automatique")
            
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR("❌ Utilisateur 'essamba.essamba' non trouvé"))
        except LearningPathTemplate.DoesNotExist:
            self.stdout.write(self.style.ERROR("❌ Template ID 4 non trouvé"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erreur: {e}"))
