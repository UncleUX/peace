from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Lister tous les utilisateurs avec leurs informations'

    def handle(self, *args, **options):
        print("👥 LISTE COMPLÈTE DES UTILISATEURS")
        print("=" * 60)
        
        users = User.objects.all()
        print(f"📊 Total utilisateurs: {users.count()}")
        print()
        
        for user in users:
            print(f"👤 {user.username}")
            print(f"   📧 Email: {user.email}")
            print(f"   🏢 Structure: {getattr(user, 'structure', 'Non définie')}")
            print(f"   🎭 Rôle: {getattr(user, 'role', 'Non défini')}")
            print(f"   📅 Créé le: {user.date_joined.strftime('%d/%m/%Y %H:%M')}")
            print(f"   🔗 Actif: {user.is_active}")
            print("-" * 40)
        
        # Chercher spécifiquement les utilisateurs avec "sango" dans le nom
        print("\n🔍 RECHERCHE SPÉCIFIQUE - 'sango'")
        sango_users = User.objects.filter(username__icontains='sango')
        
        if sango_users.exists():
            for user in sango_users:
                print(f"✅ Trouvé: {user.username} ({user.email})")
        else:
            print("❌ Aucun utilisateur trouvé avec 'sango' dans le nom")
        
        # Chercher par email
        print("\n🔍 RECHERCHE PAR EMAIL - 'sango'")
        email_users = User.objects.filter(email__icontains='sango')
        
        if email_users.exists():
            for user in email_users:
                print(f"✅ Trouvé par email: {user.username} ({user.email})")
        else:
            print("❌ Aucun utilisateur trouvé avec 'sango' dans l'email")
