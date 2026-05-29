# Implémentation technique des APIs de paiement réelles

## Fichiers à modifier/créer

### 1. **payments/services.py** (Nouveau fichier)
Créer une couche d'abstraction pour les différents fournisseurs de paiement.

### 2. **payments/views.py** (Modifier)
Remplacer la simulation dans `process_payment()` par des vrais appels API.

### 3. **payments/webhooks.py** (Nouveau fichier)
Gérer les notifications des fournisseurs (Orange Money, MTN).

### 4. **payments/urls.py** (Modifier)
Ajouter les URLs pour les webhooks et callbacks.

### 5. **crvslearning/settings.py** (Modifier)
Ajouter la configuration des clés API et URLs des fournisseurs.

### 6. **payments/tasks.py** (Nouveau fichier)
Tâches Celery pour les vérifications périodiques et retries.

### 7. **payments/tests.py** (Modifier/Étendre)
Tests pour les intégrations API.

### 8. **templates/payments/payment_detail.html** (Modifier)
Adapter l'interface pour le flux réel (instructions téléphone, temps d'attente).

## Architecture technique

### Services de paiement abstraction
- Classe `PaymentProvider` avec méthodes abstraites
- Implémentations spécifiques : `OrangeMoneyProvider`, `MTNMoneyProvider`
- Gestion uniforme des réponses et erreurs

### Flux asynchrone
- Initiation → retour immédiat avec transaction_id
- Webhook → confirmation différée (quelques minutes)
- Mise à jour du statut et attribution de l'accès

### Sécurité
- Validation des signatures webhooks
- Rate limiting sur endpoints sensibles
- Logs structurés pour audit

### Gestion des erreurs
- Mécanismes de retry automatiques
- Vérification périodique des paiements en attente
- Notifications admin pour les échecs répétés

## Configuration requise

### Variables d'environnement
```
ORANGE_MONEY_API_KEY=
ORANGE_MONEY_SECRET_KEY=
ORANGE_MONEY_WEBHOOK_URL=
MTN_MONEY_API_KEY=
MTN_MONEY_SECRET_KEY=
MTN_MONEY_WEBHOOK_URL=
```

### Dépendances additionnelles
- `requests` (appels HTTP)
- `celery` (tâches asynchrones)
- `redis` (broker pour Celery)
- `cryptography` (validation signatures)

## Étapes de déploiement

1. Obtenir les clés API des opérateurs
2. Configurer les URLs de webhook chez les fournisseurs
3. Déployer en environnement de test
4. Tests avec comptes sandbox
5. Migration vers production

## Monitoring

- Dashboard des transactions en temps réel
- Alertes sur taux d'échec élevé
- Logs centralisés des appels API
- Métriques de performance des fournisseurs



Voici l'architecture technique pour intégrer de vraies APIs de paiement dans votre projet Django :

## 1. **Structure des modèles (déjà existante)**

Les modèles `Payment`, `ModuleAccess`, `PaymentPlan` sont bien conçus pour gérer de vraies transactions :
- `Payment.transaction_id` : stockera l'ID de transaction réel du fournisseur
- `Payment.payment_method` : stockera la méthode utilisée
- `Payment.status` : suivra les états réels (pending, completed, failed)

## 2. **Intégration technique - Services de paiement**

### Créer un service d'abstraction :
```python
# payments/services.py
from abc import ABC, abstractmethod

class PaymentProvider(ABC):
    @abstractmethod
    def initiate_payment(self, amount, phone_number, reference):
        pass
    
    @abstractmethod
    def check_payment_status(self, transaction_id):
        pass

class OrangeMoneyProvider(PaymentProvider):
    def initiate_payment(self, amount, phone_number, reference):
        # Appel API Orange Money
        # Retourne transaction_id, status
        pass

class MTNMoneyProvider(PaymentProvider):
    def initiate_payment(self, amount, phone_number, reference):
        # Appel API MTN Mobile Money
        pass
```

## 3. **Configuration Django**

### Dans `settings.py` :
```python
# Configuration des APIs
PAYMENT_PROVIDERS = {
    'orange_money': {
        'api_key': 'YOUR_ORANGE_API_KEY',
        'secret_key': 'YOUR_ORANGE_SECRET',
        'webhook_url': 'https://votresite.com/payments/webhook/orange/',
        'callback_url': 'https://votresite.com/payments/callback/orange/',
    },
    'mtn_money': {
        'api_key': 'YOUR_MTN_API_KEY',
        'secret_key': 'YOUR_MTN_SECRET',
        # ...
    }
}
```

## 4. **Modification du process_payment()**

Remplacer la simulation par des vrais appels :
```python
def process_payment(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    
    payment_method = request.POST.get('payment_method')
    phone_number = request.POST.get('phone_number')
    
    # Sélection du provider
    if payment_method == 'orange_money':
        provider = OrangeMoneyProvider()
    elif payment_method == 'mtn_money':
        provider = MTNMoneyProvider()
    
    # Appel API réel
    result = provider.initiate_payment(
        amount=payment.amount,
        phone_number=phone_number,
        reference=payment.transaction_id
    )
    
    if result['success']:
        payment.status = 'completed'
        payment.transaction_id = result['transaction_id']
        payment.save()
        # Créer l'accès au module...
```

## 5. **Webhooks et callbacks**

Les fournisseurs de paiement mobile notifient votre serveur :
```python
# payments/webhooks.py
@csrf_exempt
def orange_money_webhook(request):
    # Traitement de la notification Orange Money
    transaction_data = json.loads(request.body)
    
    # Vérifier la signature
    if verify_orange_signature(transaction_data):
        payment = Payment.objects.get(
            transaction_id=transaction_data['reference']
        )
        payment.status = 'completed'
        payment.save()
        
    return HttpResponse('OK')
```

## 6. **URLs pour webhooks**
```python
# payments/urls.py
urlpatterns = [
    # ... URLs existantes
    path('webhook/orange/', views.orange_money_webhook, name='orange_webhook'),
    path('webhook/mtn/', views.mtn_money_webhook, name='mtn_webhook'),
    path('callback/orange/', views.orange_money_callback, name='orange_callback'),
]
```

## 7. **Gestion des erreurs et retries**

```python
# payments/utils.py
import requests
from django.utils import timezone
from celery import shared_task

@shared_task
def retry_payment_check(payment_id):
    """Vérifier le statut d'un paiement en attente"""
    payment = Payment.objects.get(id=payment_id)
    
    if payment.status == 'pending':
        # Appeler l'API pour vérifier le statut
        status = check_payment_status(payment.transaction_id)
        
        if status == 'completed':
            payment.status = 'completed'
            payment.save()
            # Donner l'accès au module
```

## 8. **Sécurité**

- Validation des signatures webhooks
- Tokenisation des numéros de téléphone
- Logs de toutes les transactions
- Rate limiting sur les endpoints de paiement

## 9. **Testing**

```python
# payments/tests.py
class PaymentIntegrationTest(TestCase):
    def test_orange_money_payment(self):
        # Mock l'API Orange Money
        with patch('payments.services.OrangeMoneyProvider.initiate_payment') as mock:
            mock.return_value = {'success': True, 'transaction_id': 'TXN123'}
            
            # Tester le flux complet
```

L'architecture actuelle est déjà prête pour cette intégration. Il suffit de remplacer la simulation par les vrais appels API et d'ajouter la gestion des webhooks.