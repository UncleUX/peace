from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from certifications.signals import CERTIFICATION_NOTIFICATION_CACHE, LAST_CACHE_CLEANUP

class Command(BaseCommand):
    help = 'Vérifie le statut du cache de notifications'

    def handle(self, *args, **options):
        self.stdout.write("📊 STATUT DU CACHE DE NOTIFICATIONS")
        self.stdout.write("=" * 50)
        
        # Taille actuelle du cache
        cache_size = len(CERTIFICATION_NOTIFICATION_CACHE)
        self.stdout.write(f"📦 Taille du cache: {cache_size} entrées")
        
        # Dernier nettoyage
        if LAST_CACHE_CLEANUP:
            time_since_cleanup = timezone.now() - LAST_CACHE_CLEANUP
            self.stdout.write(f"🧹 Dernier nettoyage: {time_since_cleanup.seconds} secondes")
        else:
            self.stdout.write("🧹 Dernier nettoyage: Jamais")
        
        # Détails des entrées
        if cache_size > 0:
            self.stdout.write("\n📋 Entrées dans le cache:")
            now = timezone.now()
            
            for i, (key, timestamp) in enumerate(CERTIFICATION_NOTIFICATION_CACHE.items(), 1):
                age = (now - timestamp).seconds
                age_str = f"{age}s" if age < 60 else f"{age//60}m"
                self.stdout.write(f"  {i:2d}. {key} (il y a {age_str})")
                
                if i >= 10:  # Limiter l'affichage
                    self.stdout.write(f"     ... et {cache_size - 10} autres")
                    break
        else:
            self.stdout.write("\n✅ Cache vide")
        
        # Recommandations
        self.stdout.write("\n💡 RECOMMANDATIONS:")
        if cache_size > 40:
            self.stdout.write("⚠️  Cache presque plein - nettoyage bientôt")
        elif cache_size > 20:
            self.stdout.write("✅ Cache modéré - fonctionnement normal")
        else:
            self.stdout.write("✅ Cache léger - fonctionnement optimal")
        
        # Fréquence de nettoyage
        self.stdout.write(f"\n🔄 Fréquence de nettoyage: 1 heure")
        self.stdout.write(f"⏰ Durée de rétention: 5 minutes")
        self.stdout.write(f"📊 Limite taille: 50 entrées")
