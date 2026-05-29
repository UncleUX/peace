"""
Management command pour générer automatiquement des certifications
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from courses.models import LearningPath
from certifications.utils import generate_automatic_certification, check_certification_eligibility
from certifications.models import Certification

User = get_user_model()


class Command(BaseCommand):
    help = 'Génère automatiquement des certifications pour les utilisateurs éligibles'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='ID de l\'utilisateur spécifique'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Générer pour tous les utilisateurs éligibles'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulation sans créer les certifications'
        )

    def handle(self, *args, **options):
        user_id = options.get('user_id')
        generate_all = options.get('all')
        dry_run = options.get('dry_run')
        
        self.stdout.write("🎓 Génération automatique des certifications")
        self.stdout.write("=" * 50)
        
        if user_id:
            # Générer pour un utilisateur spécifique
            self.generate_for_user(user_id, dry_run)
        elif generate_all:
            # Générer pour tous les utilisateurs éligibles
            self.generate_for_all_users(dry_run)
        else:
            self.stdout.write(self.style.ERROR("❌ Spécifiez --user-id ou --all"))
            return

    def generate_for_user(self, user_id, dry_run):
        """Génère une certification pour un utilisateur spécifique"""
        try:
            user = User.objects.get(id=user_id)
            
            if not hasattr(user, 'learning_path'):
                self.stdout.write(self.style.WARNING(f"⚠️ L'utilisateur {user.username} n'a pas de parcours"))
                return
            
            learning_path = user.learning_path
            
            if not learning_path.template:
                self.stdout.write(self.style.WARNING(f"⚠️ L'utilisateur {user.username} n'a pas de template"))
                return
            
            # Vérifier l'éligibilité
            eligibility, message = check_certification_eligibility(user, learning_path)
            
            if eligibility:
                if dry_run:
                    self.stdout.write(f"🔍 SIMULATION: {user.username} est éligible à la certification")
                else:
                    certification, result_message = generate_automatic_certification(
                        user, learning_path.template
                    )
                    
                    if certification:
                        self.stdout.write(self.style.SUCCESS(
                            f"✅ Certification générée pour {user.username}: {certification.code}"
                        ))
                    else:
                        self.stdout.write(self.style.ERROR(
                            f"❌ Erreur génération certification pour {user.username}: {result_message}"
                        ))
            else:
                self.stdout.write(self.style.WARNING(
                    f"⚠️ {user.username} n'est pas éligible: {message}"
                ))
                
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ Utilisateur ID {user_id} non trouvé"))

    def generate_for_all_users(self, dry_run):
        """Génère des certifications pour tous les utilisateurs éligibles"""
        users_with_paths = User.objects.filter(
            learning_path__isnull=False,
            learning_path__template__isnull=False
        ).select_related('learning_path', 'learning_path__template')
        
        total_users = users_with_paths.count()
        generated_count = 0
        skipped_count = 0
        
        self.stdout.write(f"📊 Analyse de {total_users} utilisateurs...")
        
        for i, user in enumerate(users_with_paths, 1):
            learning_path = user.learning_path
            
            if not learning_path.template:
                skipped_count += 1
                continue
            
            # Vérifier l'éligibilité
            eligibility, message = check_certification_eligibility(user, learning_path)
            
            if eligibility:
                if dry_run:
                    self.stdout.write(f"🔍 [{i}/{total_users}] {user.username} ÉLIGIBLE")
                    generated_count += 1
                else:
                    certification, result_message = generate_automatic_certification(
                        user, learning_path.template
                    )
                    
                    if certification:
                        self.stdout.write(self.style.SUCCESS(
                            f"✅ [{i}/{total_users}] {user.username}: {certification.code}"
                        ))
                        generated_count += 1
                    else:
                        self.stdout.write(self.style.ERROR(
                            f"❌ [{i}/{total_users}] {user.username}: Erreur"
                        ))
            else:
                skipped_count += 1
                self.stdout.write(self.style.WARNING(
                    f"⚠️ [{i}/{total_users}] {user.username}: Non éligible"
                ))
        
        # Résumé
        self.stdout.write("=" * 50)
        self.stdout.write(f"📊 RÉSUMÉ:")
        self.stdout.write(f"   • Total analysés: {total_users}")
        self.stdout.write(f"   • Certifications générées: {generated_count}")
        self.stdout.write(f"   • Non éligibles: {skipped_count}")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("🔍 MODE SIMULATION - Aucune certification créée"))
        else:
            self.stdout.write(self.style.SUCCESS("✅ Génération terminée"))
