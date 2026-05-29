from django.apps import AppConfig


class CoursesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'courses'
    
    def ready(self):
        """Importer les signaux lors du démarrage de l'application"""
        import courses.signals
