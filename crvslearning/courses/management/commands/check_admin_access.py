"""
Commande pour vérifier l'accès admin au LearningPath
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.admin import site
from courses.models import LearningPath, LearningPathTemplate
from django.contrib.contenttypes.models import ContentType

User = get_user_model()


class Command(BaseCommand):
    help = 'Vérifier l\'accès admin au LearningPath'

    def handle(self, *args, **options):
        self.stdout.write("🔍 VÉRIFICATION DE L\'ACCÈS ADMIN AU LEARNING PATH")
        self.stdout.write("=" * 60)
        
        username = 'essamba.essamba'
        
        try:
            # 1. Vérifier l'utilisateur
            user = User.objects.get(username=username)
            self.stdout.write(f"👤 Utilisateur: {user.username}")
            
            # 2. Vérifier le LearningPath
            try:
                learning_path = user.learning_path
                self.stdout.write(f"📊 LearningPath: {learning_path}")
                self.stdout.write(f"   • Template: {learning_path.template}")
                self.stdout.write(f"   • Cours actuel: {learning_path.current_course}")
                self.stdout.write(f"   • Cours complétés: {learning_path.completed_courses.count()}")
            except Exception as e:
                self.stdout.write(f"❌ Erreur LearningPath: {e}")
            
            # 3. Vérifier les permissions admin
            from django.contrib.auth.models import Permission
            from django.contrib.contenttypes.models import ContentType
            
            # Vérifier si l'utilisateur est superuser
            if user.is_superuser:
                self.stdout.write("✅ Superuser: Accès complet à l'admin")
            
            # Vérifier les permissions spécifiques
            learning_path_content_type = ContentType.objects.get_for_model(LearningPath)
            permissions = Permission.objects.filter(
                content_type=learning_path_content_type
            )
            
            if permissions.exists():
                self.stdout.write("📋 Permissions LearningPath trouvées:")
                for perm in permissions:
                    self.stdout.write(f"   • {perm.codename}: {perm.name}")
            else:
                self.stdout.write("⚠️  Aucune permission LearningPath trouvée")
            
            # 4. Vérifier l'admin site
            admin_models = site._registry
            learning_path_registered = False
            
            for model, admin_instance in admin_models.items():
                if model == LearningPath:
                    learning_path_registered = True
                    self.stdout.write(f"✅ LearningPath enregistré dans l'admin: {admin_instance}")
                    break
            
            if not learning_path_registered:
                self.stdout.write("❌ LearningPath NON enregistré dans l'admin")
            
            # 5. Vérifier les URLs
            from django.urls import reverse
            try:
                learning_path_url = reverse('admin:courses_learningpath_changelist')
                self.stdout.write(f"🔗 URL LearningPath: {learning_path_url}")
            except Exception as e:
                self.stdout.write(f"❌ Erreur URL LearningPath: {e}")
            
            # 6. Vérifier les modèles dans l'admin
            from courses.admin import LearningPathAdmin
            if hasattr(LearningPathAdmin, 'list_display'):
                self.stdout.write(f"✅ LearningPathAdmin trouvé: {LearningPathAdmin.list_display}")
            else:
                self.stdout.write("❌ LearningPathAdmin non trouvé")
                
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ Utilisateur '{username}' non trouvé"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erreur générale: {e}"))
        
        self.stdout.write("=" * 60)
        
        # 7. Solution recommandée
        self.stdout.write("🎯 SOLUTIONS RECOMMANDÉES:")
        self.stdout.write("1. Si LearningPath n'est pas dans l'admin:")
        self.stdout.write("   - Vérifier courses/admin.py")
        self.stdout.write("   - Ajouter: admin.site.register(LearningPath, LearningPathAdmin)")
        self.stdout.write("   - Redémarrer le serveur Django")
        self.stdout.write("")
        self.stdout.write("2. Si l'utilisateur n'a pas de LearningPath:")
        self.stdout.write("   - Vérifier que le template est bien assigné")
        self.stdout.write("   - Utiliser: template.assign_to_user(user)")
        self.stdout.write("")
        self.stdout.write("3. Pour vérifier rapidement:")
        self.stdout.write(f"   python manage.py check_admin_access --username {username}")
