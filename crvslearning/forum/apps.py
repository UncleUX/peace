from django.apps import AppConfig


class ForumConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'forum'
    verbose_name = 'Forum Q/R'

    def ready(self):
        """
        Importer les signaux et l'admin quand l'application est prête
        """
        try:
            import forum.admin  # Importer l'admin pour l'enregistrer
            print("Forum admin importe avec succes")
        except ImportError as e:
            print(f"Erreur import forum admin: {e}")
