# 📚 TUTORIAL : ENVOYER DES NOTIFICATIONS EN TANT QU'ADMINISTRATEUR

## 🎯 OBJECTIF
Ce tutoriel explique comment un administrateur peut envoyer des notifications personnalisées aux utilisateurs de la plateforme CRVS Learning.

---

## 🛠️ MÉTHODE 1 : VIA COMMANDE DE GESTION (RECOMMANDÉ)

### Étape 1 : Ouvrir le terminal
```bash
# Naviguez vers le dossier du projet
cd E:\Documents\Astrid\ELEARNING\crvslearning

# Activez l'environnement virtuel si nécessaire
venv\Scripts\activate
```

### Étape 2 : Envoyer à un utilisateur spécifique
```bash
python manage.py send_notification \
  --user cynthia.essomba \
  --subject "🎉 Félicitations !" \
  --message "Félicitations pour avoir terminé votre parcours de formation !" \
  --url "/certifications/" \
  --sender "Administration CRVS"
```

### Étape 3 : Envoyer à tous les utilisateurs
```bash
python manage.py send_notification \
  --all \
  --subject "📢 Annonce importante" \
  --message "Nouveaux cours disponibles sur la plateforme. Connectez-vous pour les découvrir !" \
  --url "/courses/" \
  --sender "Administration CRVS"
```

### Étape 4 : Envoyer une notification urgente
```bash
python manage.py send_notification \
  --user cynthia.essomba \
  --subject "🔐 Action requise" \
  --message "Veuillez mettre à jour votre profil pour continuer à accéder à la plateforme." \
  --url "/profile/" \
  --sender "Sécurité CRVS"
```

---

## 🖥️ MÉTHODE 2 : VIA CONSOLE DJANGO

### Étape 1 : Ouvrir la console Django
```bash
python manage.py shell
```

### Étape 2 : Importer les modèles
```python
from notifications.models import Notification
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()
```

### Étape 3 : Envoyer à un utilisateur
```python
# Trouver l'utilisateur
user = User.objects.get(username='cynthia.essomba')

# Créer la notification
notification = Notification.objects.create(
    user=user,
    subject="🎓 Nouvelle certification disponible",
    message="Félicitations ! Une nouvelle certification est disponible dans votre profil.",
    url="/certifications/",
    created_at=timezone.now()
)

print(f"✅ Notification envoyée à {user.username}")
```

### Étape 4 : Envoyer à plusieurs utilisateurs
```python
# Envoyer à tous les utilisateurs actifs
users = User.objects.filter(is_active=True)

for user in users:
    Notification.objects.create(
        user=user,
        subject="📢 Maintenance prévue",
        message="La plateforme sera en maintenance demain de 2h à 4h.",
        url="/",
        created_at=timezone.now()
    )

print(f"✅ Notifications envoyées à {users.count()} utilisateurs")
```

---

## 🎛️ MÉTHODE 3 : VIA INTERFACE ADMIN (AVANCÉ)

### Étape 1 : Créer une action admin personnalisée
Dans `notifications/admin.py` :

```python
from django.contrib import admin
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html
from .models import Notification
from django.contrib.auth import get_user_model

User = get_user_model()

@admin.action(description='Envoyer une notification personnalisée')
def send_notification_action(modeladmin, request, queryset):
    # Rediriger vers une page de formulaire
    return redirect('admin:send_notification_form')

class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'subject', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['message', 'subject']
    actions = [send_notification_action]
    
    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'send_notification_action' not in actions:
            actions.append('send_notification_action')
        return actions

admin.site.register(Notification, NotificationAdmin)
```

### Étape 2 : Créer une vue de formulaire
Dans `notifications/views.py` :

```python
from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from .models import Notification
from django.utils import timezone

User = get_user_model()

@staff_member_required
def send_notification_form(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        url = request.POST.get('url', '/dashboard/')
        
        try:
            user = User.objects.get(username=username)
            Notification.objects.create(
                user=user,
                subject=subject,
                message=message,
                url=url,
                created_at=timezone.now()
            )
            messages.success(request, f"✅ Notification envoyée à {username}")
        except User.DoesNotExist:
            messages.error(request, f"❌ Utilisateur '{username}' non trouvé")
        
        return redirect('admin:notifications_notification_changelist')
    
    return render(request, 'admin/send_notification.html')
```

---

## 📝 EXEMPLES PRATIQUES

### 🎓 Notification de félicitations
```bash
python manage.py send_notification \
  --user cynthia.essomba \
  --subject "🎉 Félicitations !" \
  --message "Félicitations pour avoir obtenu votre certification CRVS 1 - ASSOCIATE ! Votre parcours d'apprentissage est un vrai succès." \
  --url "/certifications/" \
  --sender "CRVS Learning"
```

### 🔐 Notification de sécurité
```bash
python manage.py send_notification \
  --all \
  --subject "🔐 Mise à jour de sécurité" \
  --message "Pour des raisons de sécurité, veuillez mettre à jour votre mot de passe. Connectez-vous à votre profil pour le faire." \
  --url "/password_change/" \
  --sender "Équipe de sécurité"
```

### 📢 Annonce système
```bash
python manage.py send_notification \
  --all \
  --subject "📢 Nouveaux cours disponibles" \
  --message "Découvrez nos nouveaux cours sur les techniques d'enregistrement civil. Connectez-vous pour commencer votre formation !" \
  --url "/courses/" \
  --sender "Équipe pédagogique"
```

### 🎯 Rappel d'apprentissage
```bash
python manage.py send_notification \
  --user cynthia.essomba \
  --subject "📚 Continuez votre apprentissage" \
  --message="Vous n'avez pas consulté la plateforme depuis 7 jours. De nouveaux cours vous attendent pour continuer votre formation !" \
  --url "/dashboard/" \
  --sender "CRVS Learning"
```

---

## 🎨 PERSONNALISATION AVANCÉE

### Variables dynamiques dans les messages
```python
# Dans la console Django
user = User.objects.get(username='cynthia.essomba')

# Variables personnalisées
first_name = user.first_name
last_name = user.last_name
certifications_count = user.certifications.count()

message = f"""
🎓 Bonjour {first_name} {last_name} !

Vous avez actuellement {certifications_count} certification(s) sur votre profil.

Continuez votre excellent travail !

L'équipe CRVS Learning
"""

Notification.objects.create(
    user=user,
    subject="📊 Bilan de vos certifications",
    message=message,
    url="/certifications/"
)
```

### Notifications par groupe d'utilisateurs
```python
# Envoyer aux utilisateurs avec des certifications
from django.db.models import Q

users_with_certifications = User.objects.filter(
    Q(certifications__isnull=False) | 
    Q(learning_path__isnull=False)
).distinct()

for user in users_with_certifications:
    Notification.objects.create(
        user=user,
        subject="🎓 Ressources avancées",
        message="En tant qu'utilisateur certifié, accédez à nos ressources avancées exclusives.",
        url="/advanced-resources/"
    )
```

---

## 📊 STATISTIQUES ET SUIVI

### Vérifier les notifications envoyées
```bash
# Compter les notifications par utilisateur
python manage.py shell

# Dans la console
from notifications.models import Notification
from django.db.models import Count

# Notifications par utilisateur
user_stats = Notification.objects.values('user__username').annotate(
    count=Count('id')
).order_by('-count')

for stat in user_stats[:10]:
    print(f"{stat['user__username']}: {stat['count']} notifications")

# Notifications récentes
recent = Notification.objects.order_by('-created_at')[:10]
for notif in recent:
    print(f"{notif.created_at}: {notif.user.username} - {notif.subject}")
```

---

## 🔧 DÉPANNAGE

### Problème : Utilisateur non trouvé
```bash
❌ Erreur: Utilisateur 'username' non trouvé

# Solution : Vérifier le nom d'utilisateur exact
python manage.py shell
from django.contrib.auth import get_user_model
User = get_user_model()
for user in User.objects.all():
    print(f"ID: {user.id}, Username: {user.username}, Email: {user.email}")
```

### Problème : Permission refusée
```bash
❌ Erreur: Permission refusée

# Solution : Assurez-vous d'avoir les droits d'admin
# Utilisez un compte superuser ou crée-en un
python manage.py createsuperuser
```

---

## 🎯 MEILLEURES PRATIQUES

### ✅ Recommandé
- **Tester avec un utilisateur** avant d'envoyer à tout le monde
- **Utiliser des sujets clairs** et informatifs
- **Personnaliser les messages** pour plus d'impact
- **Inclure une URL pertinente** pour l'action souhaitée
- **Éviter les notifications trop fréquentes** pour ne pas spammer

### ❌ À Éviter
- **Messages trop longs** (privilégiez la clarté)
- **URLs non fonctionnelles**
- **Notifications trop générales**
- **Envoyer à des utilisateurs inactifs**
- **Oublier de tester** avant l'envoi massif

---

## 🚀 CONCLUSION

Vous avez maintenant plusieurs méthodes pour envoyer des notifications en tant qu'administrateur :

1. **Commande de gestion** : Rapide et efficace
2. **Console Django** : Pour les tests et personnalisations
3. **Interface admin** : Pour les utilisateurs non techniques

Choisissez la méthode qui correspond le mieux à vos besoins et à votre niveau de confort technique !

---

*Pour toute question supplémentaire, n'hésitez pas à consulter la documentation ou à demander de l'aide.* 🎓
