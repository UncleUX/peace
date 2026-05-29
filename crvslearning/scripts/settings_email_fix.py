"""
Configuration email pour le développement - utilise le backend console
"""

# Configuration email pour le développement
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'noreply@crvslearning.com'
SERVER_EMAIL = 'noreply@crvslearning.com'

# Pour la production, commentez les lignes ci-dessus et décommentez ci-dessous :
"""
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'smtp.gmail.com'
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = 'votre-email@gmail.com'
# EMAIL_HOST_PASSWORD = 'votre-app-password'
# DEFAULT_FROM_EMAIL = 'noreply@crvslearning.com'
# SERVER_EMAIL = 'noreply@crvslearning.com'
"""
