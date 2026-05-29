# 📋 Système de Paiement - CRVS Learning

## 🎯 Overview

Ce document décrit le système de paiement intégré à la plateforme e-learning CRVS Learning pour conditionner l'accès aux modules de niveau avancé.

## 🏗 Architecture

### Structure de l'application `payments`

```
payments/
├── __init__.py
├── admin.py              # Interface d'administration
├── apps.py              # Configuration de l'application
├── forms.py             # Formulaires de paiement
├── middleware.py        # Middleware de contrôle d'accès
├── models.py            # Modèles de données
├── signals.py           # Signaux Django
├── templatetags/
│   ├── __init__.py
│   └── payment_tags.py  # Tags de template
├── urls.py              # URLs des routes de paiement
├── views.py             # Vues de paiement
└── migrations/          # Migrations de base de données
```

## 🗄️ Modèles de Données

### 1. Payment
Gère les transactions de paiement des utilisateurs.

```python
class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    payment_method = models.CharField(max_length=50)
    transaction_id = models.CharField(max_length=100, unique=True)
```

### 2. ModuleAccess
Contrôle l'accès aux modules payants.

```python
class ModuleAccess(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE)
    granted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
```

### 3. PaymentPlan
Définit les plans d'abonnement disponibles.

```python
class PaymentPlan(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.PositiveIntegerField()
    max_modules = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
```

### 4. Subscription
Gère les abonnements des utilisateurs.

```python
class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_subscriptions')
    plan = models.ForeignKey(PaymentPlan, on_delete=models.CASCADE)
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='plan_subscriptions')
    started_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
```

## 🔧 Configuration

### 1. Installation

L'application `payments` est déjà intégrée dans le projet :

```python
# crvslearning/settings.py
INSTALLED_APPS = [
    # ... autres applications
    'payments',  # Gestion des paiements
]
```

### 2. URLs

Les routes de paiement sont configurées :

```python
# crvslearning/urls.py
urlpatterns = [
    # ... autres routes
    path('payments/', include('payments.urls', namespace='payments')),
]
```

## 🚀 Fonctionnalités

### 1. Modules Payants Automatiques

Les modules de niveau "avancé" sont automatiquement marqués comme payants :

```python
# courses/models.py
def save(self, *args, **kwargs):
    if self.level == 'advanced' and not self.pk:
        self.is_paid = True
        if self.price == 0.00:
            self.price = 5000.00  # Prix par défaut
    super().save(*args, **kwargs)
```

### 2. Contrôle d'Accès

Le système vérifie automatiquement l'accès aux modules payants :

```python
# courses/views.py
@login_required
def module_detail(request, course_id, module_id):
    module = get_object_or_404(Module, id=module_id, course__id=course_id)
    
    if module.is_paid:
        access = ModuleAccess.objects.filter(user=request.user, module=module).first()
        if not access or not access.is_valid:
            return redirect('payments:module_payment', module_id=module.id)
```

### 3. Méthodes de Paiement Supportées

- **Orange Money** 📱
- **MTN Mobile Money** 📱  
- **Carte bancaire** 💳

## 📝 Utilisation

### 1. Créer un Module Payant

```python
# Via l'admin Django ou programmation
module = Module.objects.create(
    title="Module Avancé de Python",
    course=course,
    level="advanced",  # Automatiquement payant
    price=7500.00      # Prix personnalisé optionnel
)
```

### 2. Processus de Paiement

1. **Utilisateur tente d'accéder** à un module payant
2. **Redirection** vers la page de paiement
3. **Sélection** de la méthode de paiement
4. **Traitement** du paiement (simulé pour la démo)
5. **Création automatique** de l'accès au module
6. **Accès permanent** au contenu

### 3. Vérification d'Accès

Utiliser les template tags pour vérifier l'accès :

```html
{% load payment_tags %}

{% if request.user|has_paid_access:module %}
    <!-- Contenu du module -->
{% else %}
    <a href="{% url 'payments:module_payment' module.id %}">
        Acheter l'accès pour {{ module.price|format_price }}
    </a>
{% endif %}
```

## 🎨 Templates

### Pages de Paiement

1. **`module_payment.html`** : Page principale de paiement
2. **`payment_detail.html`** : Détails et finalisation du paiement
3. **`payment_history.html`** : Historique des paiements
4. **`my_access.html`** : Gestion des accès de l'utilisateur

### Composants

- **`module_payment_banner.html`** : Bannière d'information de paiement
- **Template tags** : Fonctions utilitaires pour les templates

## 🔐 Sécurité

### 1. Validation des Données

- Validation des numéros de téléphone camerounais
- Vérification des montants de paiement
- Protection contre les accès non autorisés

### 2. Contrôle d'Accès

- Vérification systématique de l'accès aux modules payants
- Middleware pour la protection des routes
- Redirection automatique vers la page de paiement

## 🛠 Administration

### Interface Admin Django

Accès via `/admin/` avec les modèles suivants :

- **Payments** : Gestion des transactions
- **Module Access** : Gestion des accès aux modules
- **Payment Plans** : Configuration des plans d'abonnement
- **Subscriptions** : Gestion des abonnements actifs

### Actions Disponibles

- Visualiser l'historique des paiements
- Activer/désactiver les accès
- Configurer les plans de paiement
- Exporter les données de paiement

## 📊 API Endpoints

### Vérification d'Accès

```http
GET /payments/check-access/<module_id>/
```

Response :
```json
{
    "has_access": true,
    "access_type": "paid",
    "module_title": "Module Avancé",
    "is_paid": true,
    "price": 5000.00
}
```

## 🔄 Processus de Développement

### 1. Créer les Migrations

```bash
python manage.py makemigrations payments
python manage.py makemigrations courses
python manage.py migrate
```

### 2. Tester le Système

1. Créer un module de niveau "avancé"
2. Tenter d'y accéder sans paiement
3. Suivre le processus de paiement
4. Vérifier l'accès après paiement

## 🚨 Dépannage

### Problèmes Communs

1. **Module non marqué comme payant**
   - Vérifier que le niveau est bien "advanced"
   - Confirmer le prix est supérieur à 0

2. **Accès non accordé après paiement**
   - Vérifier le statut du paiement (doit être "completed")
   - Confirmer que l'accès est actif et non expiré

3. **Redirection infinie**
   - Vérifier la configuration des URLs
   - Confirmer que le middleware est correctement configuré

### Logs

Les logs de paiement sont enregistrés dans `debug.log` :

```python
LOGGING = {
    'loggers': {
        'payments': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

## 📈 Évolutions Futures

### 1. Intégration Réelle

- Intégration avec les APIs Orange Money et MTN Mobile Money
- Support des paiements par carte bancaire (Stripe, PayPal)
- Webhooks pour la confirmation des paiements

### 2. Fonctionnalités Avancées

- Plans d'abonnement avec accès multiples
- Promotions et codes de réduction
- Paiements récurrents
- Export des factures PDF

### 3. Analytics

- Tableau de bord des revenus
- Statistiques d'utilisation des modules payants
- Rapports de conversion

## 📞 Support

Pour toute question ou problème concernant le système de paiement :

1. Consulter les logs dans `debug.log`
2. Vérifier la configuration dans `settings.py`
3. Tester avec différents scénarios d'utilisation
4. Contacter l'équipe de développement

---

**Version** : 1.0.0  
**Dernière mise à jour** : 26 janvier 2026  
**Auteur** : Équipe de développement CRVS Learning
