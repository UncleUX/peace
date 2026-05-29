from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from notifications.models import Notification
from django.urls import reverse

class Command(BaseCommand):
    help = 'Envoie une notification de test à l utilisateur Martin'

    def handle(self, *args, **options):
        """Envoie une notification à Martin"""
        
        self.stdout.write("📧 Envoi de notification à Martin...")
        self.stdout.write("=" * 50)
        
        User = get_user_model()
        martin = None
        
        # Chercher Martin par username
        try:
            martin = User.objects.get(username='martin')
            self.stdout.write(
                self.style.SUCCESS(f"✅ Martin trouvé: {martin.username} ({martin.email})")
            )
        except User.DoesNotExist:
            # Chercher par email
            try:
                martin = User.objects.get(email__icontains='martin')
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Martin trouvé par email: {martin.username} ({martin.email})")
                )
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR("❌ Martin non trouvé")
                )
                self.stdout.write("Utilisateurs disponibles:")
                for user in User.objects.all()[:10]:
                    self.stdout.write(f"   - {user.username} ({user.email})")
                return
        
        # Créer la notification
        try:
            notification = Notification.objects.create(
                user=martin,
                message="🎯 Test de notification: Ceci est une notification de test pour vérifier que le système fonctionne correctement. Vous pouvez maintenant accéder à votre parcours d'apprentissage.",
                url='/courses/learning-path/'
            )
            
            self.stdout.write(
                self.style.SUCCESS("✅ Notification envoyée avec succès !")
            )
            self.stdout.write(f"📋 ID: {notification.id}")
            self.stdout.write(f"📅 Date: {notification.created_at}")
            self.stdout.write(f"🔗 URL: {notification.url}")
            self.stdout.write(f"👤 Destinataire: {martin.username}")
            
            # Afficher le total des notifications de Martin
            total_notifications = Notification.objects.filter(user=martin).count()
            self.stdout.write(f"📊 Total des notifications pour Martin: {total_notifications}")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Erreur lors de la création de la notification: {e}")
            )
