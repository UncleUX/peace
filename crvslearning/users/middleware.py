from django.utils import timezone
from django.shortcuts import redirect
from django.urls import reverse
from django.core.cache import cache
from django.conf import settings
import json

class LastSeenMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        if request.user.is_authenticated:
            user = request.user
            now = timezone.now()
            
            # Mettre à jour le last_seen à chaque requête (plus fiable)
            # mais limiter les sauvegardes en base de données
            if not user.last_seen or (now - user.last_seen).total_seconds() > 10:
                user.last_seen = now
                user.save(update_fields=['last_seen'])
            
            # Mettre à jour le cache des utilisateurs en ligne
            cache_key = f'user_online_{user.id}'
            user_data = {
                'id': user.id,
                'username': user.username,
                'last_seen': now.isoformat(),
                'is_online': True
            }
            cache.set(cache_key, json.dumps(user_data), 60 * 5)  # 5 minutes d'expiration
        
        return response


class AdminRedirectMiddleware:
    """
    Redirige automatiquement les administrateurs vers le tableau de bord admin
    lorsqu'ils se connectent via la page de connexion normale.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Vérifier si l'utilisateur est un administrateur et s'il est sur la page d'accueil
        if (request.user.is_authenticated and 
            request.user.is_staff and 
            request.path == '/' and 
            not request.path.startswith('/admin/') and
            not request.path.startswith('/users/admin/') and
            not request.path.startswith('/static/') and
            not request.path.startswith('/media/')):
            return redirect('users:admin_dashboard')
            
        return self.get_response(request)


class UserPreferencesMiddleware:
    """
    Middleware pour gérer les préférences utilisateur via cookies
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Initialiser les préférences dans la requête
        request.user_preferences = {}
        
        # Récupérer les préférences depuis le cookie
        preferences_cookie = request.COOKIES.get('user_preferences')
        if preferences_cookie:
            try:
                request.user_preferences = json.loads(preferences_cookie)
            except json.JSONDecodeError:
                request.user_preferences = {}
        
        # Si l'utilisateur est authentifié, synchroniser avec la base de données
        if request.user.is_authenticated:
            try:
                from .models import UserPreference
                preferences, created = UserPreference.objects.get_or_create(
                    user=request.user,
                    defaults={
                        'theme': request.user_preferences.get('theme', 'light'),
                        'language': request.user_preferences.get('language', 'fr'),
                        'favorite_modules': request.user_preferences.get('favorite_modules', []),
                        'favorite_categories': request.user_preferences.get('favorite_categories', []),
                    }
                )
                
                # Mettre à jour les préférences de la requête avec celles de la BDD
                request.user_preferences.update(preferences.to_cookie_data())
                
            except Exception:
                # En cas d'erreur, utiliser les préférences du cookie
                pass
        
        response = self.get_response(request)
        
        # Sauvegarder les préférences dans le cookie si nécessaire
        if hasattr(request, '_update_preferences') and request._update_preferences:
            self._set_preferences_cookie(response, request.user_preferences)
        
        return response
    
    def _set_preferences_cookie(self, response, preferences):
        """Définit le cookie des préférences"""
        import json
        
        cookie_value = json.dumps(preferences)
        
        response.set_cookie(
            'user_preferences',
            cookie_value,
            max_age=365*24*60*60,  # 1 an en secondes
            httponly=False,  # Permettre l'accès via JavaScript
            samesite='Lax',
            secure=False  # Mettre à True en production avec HTTPS
        )
