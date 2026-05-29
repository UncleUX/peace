/**
 * Gestionnaire de consentement aux cookies
 */
class CookieConsentManager {
    constructor() {
        this.consentGiven = false;
        this.preferences = {
            necessary: true,  // Toujours vrai
            functional: false,
            analytics: false,
            marketing: false
        };
        this.consentVersion = '1.0';
        this.init();
    }

    async init() {
        // Vérifier si le consentement a déjà été donné
        const consentData = this.getConsentData();
        
        if (consentData) {
            this.consentGiven = true;
            this.preferences = { ...this.preferences, ...consentData.preferences };
            
            // Vérifier si la version du consentement est à jour
            if (consentData.version !== this.consentVersion) {
                // Nouvelle version, demander à nouveau le consentement
                this.consentGiven = false;
            }
        }

        // Si pas de consentement, afficher le modal
        if (!this.consentGiven) {
            this.showConsentModal();
        } else {
            // Appliquer les préférences existantes
            this.applyCookiePreferences();
        }

        // Configurer les écouteurs
        this.setupEventListeners();
    }

    /**
     * Récupère les données de consentement depuis localStorage
     */
    getConsentData() {
        try {
            // Essayer d'abord le cookie (spécifique à l'utilisateur)
            const cookieValue = this.getCookie('cookie_consent');
            if (cookieValue) {
                return JSON.parse(decodeURIComponent(cookieValue));
            }
            
            // Fallback sur localStorage
            const data = localStorage.getItem('cookie_consent');
            return data ? JSON.parse(data) : null;
        } catch (e) {
            console.error('Erreur lors de la lecture du consentement:', e);
            return null;
        }
    }
    
    /**
     * Récupère un cookie spécifique
     */
    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    /**
     * Sauvegarde les données de consentement dans localStorage
     */
    saveConsentData() {
        try {
            const data = {
                version: this.consentVersion,
                preferences: this.preferences,
                timestamp: new Date().toISOString(),
                userAgent: navigator.userAgent
            };
            localStorage.setItem('cookie_consent', JSON.stringify(data));
        } catch (e) {
            console.error('Erreur lors de la sauvegarde du consentement:', e);
        }
    }

    /**
     * Affiche le modal de consentement
     */
    showConsentModal() {
        // Créer le HTML du modal
        const modalHTML = this.createModalHTML();
        
        // Ajouter à la page
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
        // Afficher avec animation
        setTimeout(() => {
            document.querySelector('.cookie-consent-overlay').classList.add('show');
        }, 100);
    }

    /**
     * Crée le HTML du modal de consentement
     */
    createModalHTML() {
        return `
            <div class="cookie-consent-overlay" id="cookieConsentModal">
                <div class="cookie-consent-modal">
                    <div class="cookie-consent-header">
                        <div class="cookie-consent-icon">
                            <i class="fas fa-cookie-bite"></i>
                        </div>
                        <h2 class="cookie-consent-title">Gestion des cookies</h2>
                    </div>
                    
                    <div class="cookie-consent-content">
                        <p class="cookie-consent-text">
                            Nous utilisons des cookies pour améliorer votre expérience sur notre plateforme. 
                            Les cookies nous permettent de mémoriser vos préférences, suivre votre progression 
                            d'apprentissage et vous offrir un contenu personnalisé.
                        </p>
                        
                        <div class="cookie-consent-categories">
                            <div class="cookie-category">
                                <div class="cookie-category-header">
                                    <div class="cookie-category-title">
                                        <i class="fas fa-shield-alt"></i>
                                        Cookies essentiels
                                    </div>
                                    <label class="cookie-toggle necessary">
                                        <input type="checkbox" checked disabled>
                                        <span class="cookie-toggle-slider"></span>
                                    </label>
                                </div>
                                <p class="cookie-category-description">
                                    Ces cookies sont nécessaires au fonctionnement du site. Ils gèrent votre session, 
                                    votre authentification et les préférences essentielles.
                                </p>
                            </div>
                            
                            <div class="cookie-category">
                                <div class="cookie-category-header">
                                    <div class="cookie-category-title">
                                        <i class="fas fa-cog"></i>
                                        Cookies fonctionnels
                                    </div>
                                    <label class="cookie-toggle" data-category="functional">
                                        <input type="checkbox" id="functionalCookies">
                                        <span class="cookie-toggle-slider"></span>
                                    </label>
                                </div>
                                <p class="cookie-category-description">
                                    Ces cookies mémorisent vos préférences (thème, langue, modules favoris) 
                                    pour améliorer votre expérience utilisateur.
                                </p>
                            </div>
                            
                            <div class="cookie-category">
                                <div class="cookie-category-header">
                                    <div class="cookie-category-title">
                                        <i class="fas fa-chart-line"></i>
                                        Cookies analytiques
                                    </div>
                                    <label class="cookie-toggle" data-category="analytics">
                                        <input type="checkbox" id="analyticsCookies">
                                        <span class="cookie-toggle-slider"></span>
                                    </label>
                                </div>
                                <p class="cookie-category-description">
                                    Ces cookies nous aident à comprendre comment vous utilisez la plateforme 
                                    pour améliorer nos services.
                                </p>
                            </div>
                            
                            <div class="cookie-category">
                                <div class="cookie-category-header">
                                    <div class="cookie-category-title">
                                        <i class="fas fa-bullhorn"></i>
                                        Cookies marketing
                                    </div>
                                    <label class="cookie-toggle" data-category="marketing">
                                        <input type="checkbox" id="marketingCookies">
                                        <span class="cookie-toggle-slider"></span>
                                    </label>
                                </div>
                                <p class="cookie-category-description">
                                    Ces cookies sont utilisés pour vous proposer des contenus pertinents 
                                    et des offres personnalisées.
                                </p>
                            </div>
                        </div>
                    </div>
                    
                    <div class="cookie-consent-actions">
                        <button class="btn-cookie btn-cookie-outline" onclick="cookieConsent.showDetails()">
                            En savoir plus
                        </button>
                        <button class="btn-cookie btn-cookie-secondary" onclick="cookieConsent.acceptOnlyNecessary()">
                            Refuser
                        </button>
                        <button class="btn-cookie btn-cookie-primary" onclick="cookieConsent.acceptAll()">
                            Tout accepter
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Configure les écouteurs d'événements
     */
    setupEventListeners() {
        // Écouteurs pour les toggles
        document.addEventListener('change', (e) => {
            if (e.target.matches('.cookie-toggle input:not([disabled])')) {
                const toggle = e.target.closest('.cookie-toggle');
                const category = toggle.getAttribute('data-category');
                
                if (category) {
                    this.preferences[category] = e.target.checked;
                    toggle.classList.toggle('enabled', e.target.checked);
                }
            }
        });

        // Fermeture du modal en cliquant sur l'overlay
        document.addEventListener('click', (e) => {
            if (e.target.matches('.cookie-consent-overlay')) {
                // Ne pas fermer si on clique sur le modal lui-même
                if (!e.target.closest('.cookie-consent-modal')) {
                    this.showReminder();
                }
            }
        });
    }

    /**
     * Accepte tous les cookies
     */
    acceptAll() {
        this.preferences = {
            necessary: true,
            functional: true,
            analytics: true,
            marketing: true
        };
        
        this.saveConsent();
        this.hideModal();
        this.applyCookiePreferences();
        this.showSuccessMessage('Tous les cookies ont été acceptés');
    }

    /**
     * Accepte uniquement les cookies essentiels
     */
    acceptOnlyNecessary() {
        this.preferences = {
            necessary: true,
            functional: false,
            analytics: false,
            marketing: false
        };
        
        this.saveConsent();
        this.hideModal();
        this.applyCookiePreferences();
        this.showSuccessMessage('Seuls les cookies essentiels ont été acceptés');
    }

    /**
     * Accepte les préférences personnalisées
     */
    acceptCustom() {
        this.saveConsent();
        this.hideModal();
        this.applyCookiePreferences();
        this.showSuccessMessage('Vos préférences ont été enregistrées');
    }

    /**
     * Sauvegarde le consentement
     */
    saveConsent() {
        this.consentGiven = true;
        this.saveConsentData();
        
        // Mettre à jour le cookie de consentement pour le serveur
        this.setConsentCookie();
    }

    /**
     * Définit le cookie de consentement pour le serveur
     */
    setConsentCookie() {
        const consentData = {
            version: this.consentVersion,
            preferences: this.preferences,
            timestamp: new Date().toISOString()
        };
        
        document.cookie = `cookie_consent=${encodeURIComponent(JSON.stringify(consentData))}; max-age=365*24*60*60; path=/; samesite=Lax`;
    }

    /**
     * Applique les préférences de cookies
     */
    applyCookiePreferences() {
        // Cookies fonctionnels : activer les préférences utilisateur
        if (this.preferences.functional) {
            this.enableFunctionalCookies();
        } else {
            this.disableFunctionalCookies();
        }
        
        // Cookies analytiques : activer le suivi
        if (this.preferences.analytics) {
            this.enableAnalyticsCookies();
        } else {
            this.disableAnalyticsCookies();
        }
        
        // Cookies marketing : activer le marketing
        if (this.preferences.marketing) {
            this.enableMarketingCookies();
        } else {
            this.disableMarketingCookies();
        }
        
        // Déclencher un événement pour les autres scripts
        document.dispatchEvent(new CustomEvent('cookieConsentApplied', {
            detail: { preferences: this.preferences }
        }));
    }

    /**
     * Active les cookies fonctionnels
     */
    enableFunctionalCookies() {
        // Activer le gestionnaire de préférences utilisateur
        if (window.userPreferences) {
            window.userPreferences.enabled = true;
        }
        
        // Activer d'autres fonctionnalités
        document.body.classList.add('functional-cookies-enabled');
    }

    /**
     * Désactive les cookies fonctionnels
     */
    disableFunctionalCookies() {
        // Désactiver le gestionnaire de préférences
        if (window.userPreferences) {
            window.userPreferences.enabled = false;
        }
        
        document.body.classList.remove('functional-cookies-enabled');
    }

    /**
     * Active les cookies analytiques
     */
    enableAnalyticsCookies() {
        // Initialiser Google Analytics ou autre outil d'analyse
        if (typeof gtag !== 'undefined') {
            gtag('consent', 'update', {
                'analytics_storage': 'granted'
            });
        }
        
        document.body.classList.add('analytics-cookies-enabled');
    }

    /**
     * Désactive les cookies analytiques
     */
    disableAnalyticsCookies() {
        if (typeof gtag !== 'undefined') {
            gtag('consent', 'update', {
                'analytics_storage': 'denied'
            });
        }
        
        document.body.classList.remove('analytics-cookies-enabled');
    }

    /**
     * Active les cookies marketing
     */
    enableMarketingCookies() {
        if (typeof gtag !== 'undefined') {
            gtag('consent', 'update', {
                'ad_storage': 'granted',
                'ad_user_data': 'granted',
                'ad_personalization': 'granted'
            });
        }
        
        document.body.classList.add('marketing-cookies-enabled');
    }

    /**
     * Désactive les cookies marketing
     */
    disableMarketingCookies() {
        if (typeof gtag !== 'undefined') {
            gtag('consent', 'update', {
                'ad_storage': 'denied',
                'ad_user_data': 'denied',
                'ad_personalization': 'denied'
            });
        }
        
        document.body.classList.remove('marketing-cookies-enabled');
    }

    /**
     * Cache le modal de consentement
     */
    hideModal() {
        const modal = document.querySelector('.cookie-consent-overlay');
        if (modal) {
            modal.classList.remove('show');
            setTimeout(() => {
                modal.remove();
            }, 300);
        }
    }

    /**
     * Affiche un rappel
     */
    showReminder() {
        this.showInfoMessage('Veuillez choisir vos préférences de cookies pour continuer');
    }

    /**
     * Affiche les détails
     */
    showDetails() {
        // Ouvrir une page avec plus de détails ou développer une section
        window.open('/privacy-policy#cookies', '_blank');
    }

    /**
     * Affiche un message de succès
     */
    showSuccessMessage(message) {
        this.showToast(message, 'success');
    }

    /**
     * Affiche un message d'information
     */
    showInfoMessage(message) {
        this.showToast(message, 'info');
    }

    /**
     * Affiche un toast
     */
    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : 'info-circle'}"></i>
            <span>${message}</span>
        `;
        
        document.body.appendChild(toast);
        
        setTimeout(() => toast.classList.add('show'), 10);
        
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    /**
     * Réinitialise le consentement (pour les tests)
     */
    resetConsent() {
        localStorage.removeItem('cookie_consent');
        document.cookie = 'cookie_consent=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
        this.consentGiven = false;
        this.preferences = {
            necessary: true,
            functional: false,
            analytics: false,
            marketing: false
        };
        this.showConsentModal();
    }

    /**
     * Vérifie si une catégorie de cookies est acceptée
     */
    hasConsent(category) {
        return this.preferences[category] || false;
    }
}

// Initialiser le gestionnaire de consentement
document.addEventListener('DOMContentLoaded', () => {
    window.cookieConsent = new CookieConsentManager();
});

// Exporter pour utilisation dans d'autres scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CookieConsentManager;
}
