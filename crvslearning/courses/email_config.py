"""
Configuration des emails pour les notifications de parcours d'apprentissage
"""

# Configuration des emails pour le développement
EMAIL_CONFIG = {
    'development': {
        'EMAIL_BACKEND': 'django.core.mail.backends.console.EmailBackend',
        'DEFAULT_FROM_EMAIL': 'noreply@crvslearning.com',
        'SITE_NAME': 'CRVS Learning - Développement',
        'SITE_URL': 'http://127.0.0.1:8000',
    },
    'production': {
        'EMAIL_BACKEND': 'django.core.mail.backends.smtp.EmailBackend',
        'EMAIL_HOST': 'smtp.gmail.com',  # À configurer selon votre provider
        'EMAIL_PORT': 587,
        'EMAIL_USE_TLS': True,
        'EMAIL_HOST_USER': 'votre-email@gmail.com',  # À configurer
        'EMAIL_HOST_PASSWORD': 'votre-mot-de-passe',  # À configurer
        'DEFAULT_FROM_EMAIL': 'noreply@crvslearning.com',
        'SITE_NAME': 'CRVS Learning',
        'SITE_URL': 'https://votre-domaine.com',
    }
}

def get_email_config(environment='development'):
    """Retourne la configuration email selon l'environnement"""
    return EMAIL_CONFIG.get(environment, EMAIL_CONFIG['development'])

def setup_email_settings(settings, environment='development'):
    """Configure les settings Django pour les emails"""
    config = get_email_config(environment)
    
    for key, value in config.items():
        setattr(settings, key, value)
    
    # Configuration supplémentaire pour les emails
    settings.EMAIL_SUBJECT_PREFIX = '[CRVS Learning] '
    settings.SERVER_EMAIL = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@crvslearning.com')
    
    return config

# Templates d'email par défaut
DEFAULT_EMAIL_TEMPLATES = {
    'new_learning_path': {
        'subject': '🎯 Nouveau parcours d\'apprentissage disponible',
        'message': 'Un nouveau parcours d\'apprentissage est disponible pour vous.',
    },
    'course_completed': {
        'subject': '🎉 Cours terminé avec succès',
        'message': 'Félicitations ! Vous avez terminé un cours de votre parcours.',
    },
    'learning_path_completed': {
        'subject': '🏆 Parcours d\'apprentissage terminé',
        'message': 'Félicitations ! Vous avez terminé votre parcours d\'apprentissage.',
    }
}

def get_default_email_template(template_type):
    """Retourne le template d'email par défaut"""
    return DEFAULT_EMAIL_TEMPLATES.get(template_type, {})
