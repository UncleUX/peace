/**
 * Gestionnaire des préférences utilisateur avec support cookies
 */
class UserPreferencesManager {
    constructor() {
        this.preferences = {};
        this.init();
    }

    /**
     * Initialise le gestionnaire de préférences
     */
    async init() {
        // Charger les préférences depuis le cookie
        this.loadFromCookie();
        
        // Si l'utilisateur est connecté, synchroniser avec le serveur
        if (this.isUserLoggedIn()) {
            await this.syncWithServer();
        }
        
        // Appliquer les préférences immédiatement
        this.applyPreferences();
        
        // Configurer les écouteurs d'événements
        this.setupEventListeners();
    }

    /**
     * Vérifie si l'utilisateur est connecté
     */
    isUserLoggedIn() {
        return document.body.classList.contains('user-logged-in') || 
               document.querySelector('meta[name="user-logged-in"]')?.content === 'true';
    }

    /**
     * Charge les préférences depuis le cookie
     */
    loadFromCookie() {
        const cookieValue = this.getCookie('user_preferences');
        if (cookieValue) {
            try {
                this.preferences = JSON.parse(cookieValue);
            } catch (e) {
                console.error('Erreur lors du chargement des préférences:', e);
                this.preferences = {};
            }
        }
    }

    /**
     * Récupère la valeur d'un cookie
     */
    getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }

    /**
     * Définit un cookie
     */
    setCookie(name, value, days = 365) {
        const date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
        const expires = `expires=${date.toUTCString()}`;
        document.cookie = `${name}=${value};${expires};path=/;samesite=Lax`;
    }

    /**
     * Synchronise les préférences avec le serveur
     */
    async syncWithServer() {
        try {
            const response = await fetch('/users/api/preferences/');
            const data = await response.json();
            
            if (data.status === 'success') {
                this.preferences = { ...this.preferences, ...data.preferences };
                this.saveToCookie();
                this.applyPreferences();
            }
        } catch (error) {
            console.error('Erreur de synchronisation:', error);
        }
    }

    /**
     * Sauvegarde les préférences dans le cookie
     */
    saveToCookie() {
        this.setCookie('user_preferences', JSON.stringify(this.preferences));
    }

    /**
     * Applique les préférences à l'interface
     */
    applyPreferences() {
        // Appliquer le thème
        this.applyTheme();
        
        // Appliquer la langue
        this.applyLanguage();
        
        // Appliquer les autres préférences
        this.applyOtherPreferences();
    }

    /**
     * Applique le thème (clair/sombre)
     */
    applyTheme() {
        const theme = this.preferences.theme || 'light';
        document.body.setAttribute('data-theme', theme);
        
        // Mettre à jour les boutons de thème
        document.querySelectorAll('[data-theme-toggle]').forEach(btn => {
            btn.classList.toggle('active', btn.getAttribute('data-theme') === theme);
        });
    }

    /**
     * Applique la langue
     */
    applyLanguage() {
        const language = this.preferences.language || 'fr';
        
        // Mettre à jour l'attribut lang
        document.documentElement.setAttribute('lang', language);
        
        // Mettre à jour les sélecteurs de langue
        document.querySelectorAll('[data-language-select]').forEach(select => {
            select.value = language;
        });
    }

    /**
     * Applique les autres préférences
     */
    applyOtherPreferences() {
        // Auto-play vidéo
        if (this.preferences.auto_play_video) {
            document.body.classList.add('auto-play-video');
        }

        // Affichage de la progression
        if (this.preferences.show_progress) {
            document.body.classList.add('show-progress');
        }

        // Notifications
        this.updateNotificationSettings();
    }

    /**
     * Met à jour les paramètres de notification
     */
    updateNotificationSettings() {
        // Cette fonction peut être étendue pour gérer les notifications push/email
        const emailNotif = this.preferences.email_notifications !== false;
        const pushNotif = this.preferences.push_notifications !== false;
        
        document.body.classList.toggle('email-notifications', emailNotif);
        document.body.classList.toggle('push-notifications', pushNotif);
    }

    /**
     * Configure les écouteurs d'événements
     */
    setupEventListeners() {
        // Boutons de thème
        document.querySelectorAll('[data-theme-toggle]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const theme = btn.getAttribute('data-theme');
                this.updatePreference('theme', theme);
            });
        });

        // Sélecteurs de langue
        document.querySelectorAll('[data-language-select]').forEach(select => {
            select.addEventListener('change', (e) => {
                this.updatePreference('language', e.target.value);
            });
        });

        // Boutons favoris pour les modules
        document.querySelectorAll('[data-favorite-module]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const moduleId = btn.getAttribute('data-module-id');
                this.toggleFavoriteModule(moduleId);
            });
        });

        // Boutons favoris pour les catégories
        document.querySelectorAll('[data-favorite-category]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const categoryId = btn.getAttribute('data-category-id');
                this.toggleFavoriteCategory(categoryId);
            });
        });

        // Autres préférences
        document.querySelectorAll('[data-preference]').forEach(input => {
            input.addEventListener('change', (e) => {
                const key = input.getAttribute('data-preference');
                const value = input.type === 'checkbox' ? input.checked : input.value;
                this.updatePreference(key, value);
            });
        });
    }

    /**
     * Met à jour une préférence
     */
    async updatePreference(key, value) {
        this.preferences[key] = value;
        this.saveToCookie();
        this.applyPreferences();

        // Si l'utilisateur est connecté, synchroniser avec le serveur
        if (this.isUserLoggedIn()) {
            await this.syncPreferenceToServer(key, value);
        }

        // Déclencher un événement personnalisé
        document.dispatchEvent(new CustomEvent('preferenceUpdated', {
            detail: { key, value }
        }));
    }

    /**
     * Synchronise une préférence spécifique avec le serveur
     */
    async syncPreferenceToServer(key, value) {
        try {
            const formData = new FormData();
            formData.append('key', key);
            formData.append('value', value);

            const response = await fetch('/users/api/update-session-preference/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            const data = await response.json();
            if (data.status !== 'success') {
                console.error('Erreur de synchronisation:', data.message);
            }
        } catch (error) {
            console.error('Erreur de synchronisation:', error);
        }
    }

    /**
     * Récupère le token CSRF
     */
    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
               this.getCookie('csrftoken');
    }

    /**
     * Bascule le statut favori d'un module
     */
    async toggleFavoriteModule(moduleId) {
        if (!this.isUserLoggedIn()) {
            this.showLoginMessage();
            return;
        }

        try {
            const formData = new FormData();
            formData.append('module_id', moduleId);

            const response = await fetch('/users/api/toggle-favorite-module/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            const data = await response.json();
            
            if (data.status === 'success') {
                // Mettre à jour la liste des favoris
                const favorites = this.preferences.favorite_modules || [];
                const index = favorites.indexOf(moduleId);
                
                if (data.is_favorite && index === -1) {
                    favorites.push(moduleId);
                } else if (!data.is_favorite && index > -1) {
                    favorites.splice(index, 1);
                }
                
                this.preferences.favorite_modules = favorites;
                this.saveToCookie();
                
                // Mettre à jour l'interface
                this.updateFavoriteButton(moduleId, data.is_favorite);
                
                // Afficher un message
                this.showMessage(data.message, 'success');
            } else {
                this.showMessage(data.message, 'error');
            }
        } catch (error) {
            console.error('Erreur:', error);
            this.showMessage('Une erreur est survenue', 'error');
        }
    }

    /**
     * Bascule le statut favori d'une catégorie
     */
    async toggleFavoriteCategory(categoryId) {
        if (!this.isUserLoggedIn()) {
            this.showLoginMessage();
            return;
        }

        try {
            const formData = new FormData();
            formData.append('category_id', categoryId);

            const response = await fetch('/users/api/toggle-favorite-category/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            const data = await response.json();
            
            if (data.status === 'success') {
                // Mettre à jour la liste des favoris
                const favorites = this.preferences.favorite_categories || [];
                const index = favorites.indexOf(categoryId);
                
                if (data.is_favorite && index === -1) {
                    favorites.push(categoryId);
                } else if (!data.is_favorite && index > -1) {
                    favorites.splice(index, 1);
                }
                
                this.preferences.favorite_categories = favorites;
                this.saveToCookie();
                
                // Mettre à jour l'interface
                this.updateFavoriteButton(categoryId, data.is_favorite, 'category');
                
                // Afficher un message
                this.showMessage(data.message, 'success');
            } else {
                this.showMessage(data.message, 'error');
            }
        } catch (error) {
            console.error('Erreur:', error);
            this.showMessage('Une erreur est survenue', 'error');
        }
    }

    /**
     * Met à jour l'état d'un bouton favori
     */
    updateFavoriteButton(id, isFavorite, type = 'module') {
        const selector = type === 'module' 
            ? `[data-favorite-module][data-module-id="${id}"]`
            : `[data-favorite-category][data-category-id="${id}"]`;
            
        document.querySelectorAll(selector).forEach(btn => {
            btn.classList.toggle('active', isFavorite);
            
            // Mettre à jour l'icône
            const icon = btn.querySelector('i') || btn;
            if (icon) {
                icon.className = isFavorite ? 'fas fa-heart' : 'far fa-heart';
            }
            
            // Mettre à jour le texte
            const text = btn.querySelector('.favorite-text');
            if (text) {
                text.textContent = isFavorite ? 'Retirer des favoris' : 'Ajouter aux favoris';
            }
        });
    }

    /**
     * Vérifie si un module est en favori
     */
    isModuleFavorite(moduleId) {
        return (this.preferences.favorite_modules || []).includes(moduleId);
    }

    /**
     * Vérifie si une catégorie est en favori
     */
    isCategoryFavorite(categoryId) {
        return (this.preferences.favorite_categories || []).includes(categoryId);
    }

    /**
     * Affiche un message à l'utilisateur
     */
    showMessage(message, type = 'info') {
        // Créer une notification toast
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        
        document.body.appendChild(toast);
        
        // Animation d'entrée
        setTimeout(() => toast.classList.add('show'), 10);
        
        // Suppression après 3 secondes
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    /**
     * Affiche un message de connexion requise
     */
    showLoginMessage() {
        this.showMessage('Vous devez être connecté pour ajouter des favoris', 'warning');
    }

    /**
     * Récupère une préférence
     */
    get(key, defaultValue = null) {
        return this.preferences[key] !== undefined ? this.preferences[key] : defaultValue;
    }

    /**
     * Réinitialise toutes les préférences
     */
    reset() {
        this.preferences = {
            theme: 'light',
            language: 'fr',
            favorite_modules: [],
            favorite_categories: [],
            email_notifications: true,
            push_notifications: true,
            auto_play_video: false,
            show_progress: true
        };
        
        this.saveToCookie();
        this.applyPreferences();
        this.showMessage('Préférences réinitialisées', 'success');
    }
}

// Initialiser le gestionnaire de préférences quand le DOM est chargé
document.addEventListener('DOMContentLoaded', () => {
    window.userPreferences = new UserPreferencesManager();
});

// Exporter pour utilisation dans d'autres scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = UserPreferencesManager;
}
