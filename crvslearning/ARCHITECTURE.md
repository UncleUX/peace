# 📋 DOCUMENT TECHNIQUE : ARCHITECTURE DE LA PLATEFORME CRVS LEARNING

---

## 🏗️ ARCHITECTURE GLOBALE

### Vue d'ensemble du système
```
┌─────────────────────────────────────────────────────────────────┐
│                    ARCHITECTURE CRVS LEARNING                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  🌐 FRONTEND (Django Templates + Bootstrap 5)                  │
│  ├─ Forum (questions, réponses, membres)                        │
│  ├─ Cours (modules, leçons, évaluations)                       │
│  ├─ Paiements (Orange Money, MTN, Carte bancaire)               │
│  ├─ Notifications (alertes, messages)                           │
│  └─ Profil utilisateur (personnel, professionnel)               │
│                                                                 │
│  🔧 BACKEND (Django Framework)                                  │
│  ├─ Gestion des utilisateurs (CustomUser)                       │
│  ├─ Système de cours (Course, Module, Lesson)                   │
│  ├─ Forum (Question, Answer, Comment)                          │
│  ├─ Paiements (Payment, ModuleAccess, Subscription)             │
│  ├─ Évaluations (Quiz, Test, Certification)                    │
│  └─ Notifications (Email, In-app)                              │
│                                                                 │
│  🗄️ BASE DE DONNÉES (PostgreSQL)                               │
│  ├─ Utilisateurs et profils                                     │
│  ├─ Contenu pédagogique                                         │
│  ├─ Activités du forum                                          │
│  ├─ Transactions financières                                    │
│  └─ Historique des interactions                                │
│                                                                 │
│  📦 SERVICES EXTERNES                                           │
│  ├─ Orange Money API                                            │
│  ├─ MTN Mobile Money API                                        │
│  ├─ Service d'emails (SMTP)                                     │
│  └─ Stockage de fichiers (Media)                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🧱 COMPOSANTS TECHNIQUES

### 1. Framework et Technologies
```yaml
Backend:
  - Django 5.2.8 (Python 3.12)
  - Django REST Framework (API endpoints)
  - Celery (tâches asynchrones)
  - Redis (cache et broker)
  
Frontend:
  - Django Templates
  - Bootstrap 5.3
  - JavaScript (Vanilla JS)
  - SweetAlert2 (notifications)
  - Chart.js (statistiques)
  
Base de données:
  - PostgreSQL (principal)
  - SQLite (développement)
  
Infrastructure:
  - Docker & Docker Compose
  - Nginx (reverse proxy)
  - Gunicorn (WSGI server)
  - Uvicorn (ASGI server)
```

### 2. Structure des applications Django
```
crvslearning/
├── manage.py
├── crvslearning/          # Configuration principale
│   ├── settings/
│   │   ├── base.py       # Configuration de base
│   │   ├── development.py # Développement
│   │   ├── production.py # Production
│   │   └── testing.py    # Tests
│   ├── urls.py          # URLs globales
│   ├── wsgi.py          # WSGI
│   └── asgi.py          # ASGI
│
├── users/                # Gestion des utilisateurs
│   ├── models.py        # CustomUser, Profile
│   ├── views.py         # Inscription, connexion, profil
│   ├── forms.py         # Formulaires utilisateur
│   └── urls.py          # URLs utilisateurs
│
├── courses/              # Système de cours
│   ├── models.py        # Course, Module, Lesson
│   ├── views.py         # Cours, modules, leçons
│   ├── forms.py         # Formulaires cours
│   └── urls.py          # URLs cours
│
├── forum/               # Forum de discussion
│   ├── models.py        # Question, Answer, Comment
│   ├── views.py         # Forum, questions, réponses
│   ├── forms.py         # Formulaires forum
│   └── urls.py          # URLs forum
│
├── payments/            # Système de paiement
│   ├── models.py        # Payment, ModuleAccess, Subscription
│   ├── views.py         # Paiements, historique
│   ├── services.py      # API Orange Money, MTN
│   └── urls.py          # URLs paiements
│
├── evaluations/         # Évaluations et tests
│   ├── models.py        # Quiz, Question, Answer, Result
│   ├── views.py         # Tests, résultats
│   ├── forms.py         # Formulaires évaluations
│   └── urls.py          # URLs évaluations
│
├── notifications/       # Système de notifications
│   ├── models.py        # Notification, Message
│   ├── views.py         # Notifications, messages
│   ├── services.py      # Email, SMS
│   └── urls.py          # URLs notifications
│
└── static/              # Fichiers statiques
    ├── css/
    ├── js/
    ├── img/
    └── vendor/
```

---

## 🔄 MODE DE COMMUNICATION

### 1. Architecture de communication
```
┌─────────────────────────────────────────────────────────────────┐
│                    FLUX DE COMMUNICATION                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  🌐 CLIENT ↔ DJANGO (HTTP/HTTPS)                               │
│  ├─ Requêtes web (GET, POST, PUT, DELETE)                      │
│  ├─ Soumission de formulaires                                   │
│  ├─ Upload de fichiers                                          │
│  ├─ Authentification (sessions)                                 │
│  └─ WebSocket (notifications temps réel)                        │
│                                                                 │
│  🐍 DJANGO ↔ SERVICES EXTERNES                                  │
│  ├─ API Orange Money (REST)                                    │
│  ├─ API MTN Mobile Money (REST)                                │
│  ├─ SMTP (Email)                                               │
│  ├─ Redis (Cache + Queue)                                      │
│  └─ PostgreSQL (Base de données)                                │
│                                                                 │
│  🔄 DJANGO INTERNAL                                             │
│  ├─ Models ↔ Database (ORM)                                    │
│  ├─ Views ↔ Templates (Render)                                  │
│  ├─ Signals (Hooks automatiques)                                │
│  ├─ Middleware (Processing pipeline)                            │
│  └─ Celery Tasks (Async processing)                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2. Protocoles et formats
```yaml
Communication:
  Protocol: HTTP/HTTPS
  Format: JSON (API), HTML (Templates)
  Authentication: Django Sessions + JWT (API)
  CORS: Configuré pour les appels cross-origin
  
API Externes:
  Orange Money: REST API + OAuth 2.0
  MTN Mobile Money: REST API + API Key
  Email: SMTP (TLS/SSL)
  
Real-time:
  WebSocket: Django Channels
  Redis Pub/Sub: Notifications temps réel
```

---

## 🗄️ MODÈLE DE DONNÉES

### 1. Schéma de la base de données
```sql
-- UTILISATEURS
users_customuser:
  id (PK)
  username (UNIQUE)
  email (UNIQUE)
  first_name
  last_name
  date_of_birth
  is_active
  is_staff
  date_joined
  last_login

users_profile:
  user_id (FK -> users_customuser)
  avatar
  bio
  phone
  structure
  service
  created_at
  updated_at

-- COURS
courses_course:
  id (PK)
  title
  description
  created_at
  updated_at

courses_module:
  id (PK)
  course_id (FK -> courses_course)
  title
  description
  level (basic, intermediate, advanced)
  is_paid
  price
  order
  created_at
  updated_at

courses_lesson:
  id (PK)
  module_id (FK -> courses_module)
  title
  content (TEXT)
  video_url
  order
  created_at
  updated_at

-- FORUM
forum_question:
  id (PK)
  title
  content (TEXT)
  author_id (FK -> users_customuser)
  category_id (FK -> forum_category)
  is_closed
  is_validated
  views_count
  total_votes
  created_at
  updated_at

forum_answer:
  id (PK)
  question_id (FK -> forum_question)
  content (TEXT)
  author_id (FK -> users_customuser)
  is_validated
  total_votes
  created_at
  updated_at

forum_comment:
  id (PK)
  answer_id (FK -> forum_answer)
  content (TEXT)
  author_id (FK -> users_customuser)
  created_at
  updated_at

-- PAIEMENTS
payments_payment:
  id (PK)
  user_id (FK -> users_customuser)
  module_id (FK -> courses_module)
  amount
  method (orange_money, mtn, card)
  status (pending, completed, failed)
  transaction_id
  created_at
  updated_at

payments_moduleaccess:
  id (PK)
  user_id (FK -> users_customuser)
  module_id (FK -> courses_module)
  payment_id (FK -> payments_payment)
  access_granted_at
  expires_at

-- ÉVALUATIONS
evaluations_quiz:
  id (PK)
  title
  description
  module_id (FK -> courses_module)
  created_at
  updated_at

evaluations_question:
  id (PK)
  quiz_id (FK -> evaluations_quiz)
  text
  question_type (multiple_choice, true_false, text)
  created_at
  updated_at

evaluations_answer:
  id (PK)
  question_id (FK -> evaluations_question)
  text
  is_correct
  created_at
  updated_at

evaluations_result:
  id (PK)
  user_id (FK -> users_customuser)
  quiz_id (FK -> evaluations_quiz)
  score
  total_questions
  correct_answers
  completed_at
  created_at

-- NOTIFICATIONS
notifications_notification:
  id (PK)
  user_id (FK -> users_customuser)
  title
  message
  type (info, success, warning, error)
  is_read
  created_at
```

---

## 🔐 SÉCURITÉ

### 1. Mesures de sécurité
```yaml
Authentication:
  - Django Authentication System
  - Password hashing (PBKDF2)
  - Session management
  - CSRF protection
  - Security headers

Authorization:
  - Django Permissions Framework
  - Role-based access control
  - Custom decorators
  - Middleware permissions

Data Protection:
  - Input validation
  - SQL injection prevention (ORM)
  - XSS protection
  - File upload security
  - Rate limiting

API Security:
  - API Key management
  - OAuth 2.0 (services externes)
  - JWT tokens (optionnel)
  - HTTPS enforcement
```

### 2. Configuration de sécurité
```python
# settings/base.py
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# CSRF
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_TRUSTED_ORIGINS = ['https://votredomaine.com']

# Session
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 86400  # 24 heures
```

---

## 📊 PERFORMANCE ET OPTIMISATION

### 1. Optimisation de la base de données
```yaml
Indexation:
  - Index sur les clés étrangères
  - Index sur les champs de recherche
  - Index composite (user + timestamp)
  - Index full-text (recherche)

Caching:
  - Redis cache (sessions, données fréquemment utilisées)
  - Template caching
  - Database query caching
  - CDN pour les assets statiques

Database:
  - Connection pooling
  - Query optimization
  - Select_related/Prefetch_related
  - Bulk operations
```

### 2. Performance frontend
```yaml
Optimisation:
  - CSS/JS minification
  - Image optimization
  - Lazy loading
  - Compression (gzip/brotli)
  - Browser caching

Monitoring:
  - Django Debug Toolbar (développement)
  - Sentry (erreurs production)
  - Logging structuré
  - Métriques de performance
```

---

## 🚀 DÉPLOIEMENT

### 1. Architecture de déploiement
```yaml
Production:
  - Docker containers
  - Nginx (reverse proxy + load balancer)
  - Gunicorn (WSGI server)
  - PostgreSQL (database)
  - Redis (cache + broker)
  - Celery workers
  - Monitoring (Prometheus + Grafana)

Infrastructure:
  - Cloud provider (AWS, GCP, Azure)
  - Auto-scaling
  - Load balancing
  - SSL/TLS certificates
  - Backup strategy
```

### 2. Docker Compose
```yaml
# docker-compose.yml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEBUG=False
      - DATABASE_URL=postgresql://user:pass@db:5432/crvs
    depends_on:
      - db
      - redis

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=crvs
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  celery:
    build: .
    command: celery -A crvslearning worker -l info
    depends_on:
      - db
      - redis

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - web
```

---

## 📈 MONITORING ET LOGGING

### 1. Surveillance système
```yaml
Métriques:
  - Response time
  - Error rate
  - Database performance
  - Memory usage
  - CPU usage
  - Active users

Logs:
  - Structured logging (JSON)
  - Error tracking (Sentry)
  - Access logs
  - Application logs
  - Security logs
```

### 2. Alertes
```yaml
Alerting:
  - High error rate
  - Database connection issues
  - Payment processing failures
  - Resource exhaustion
  - Security incidents
```

---

## 🔄 FLUX DE TRAVAIL

### 1. Cycle de vie d'une transaction
```
1. UTILISATEUR → DJANGO
   - Navigation sur le site
   - Authentification
   - Accès aux cours

2. DJANGO → BASE DE DONNÉES
   - Requêtes SQL via ORM
   - Validation des données
   - Sauvegarde des modifications

3. DJANGO → SERVICES EXTERNES
   - Paiement (Orange Money/MTN)
   - Envoi d'emails
   - Notifications

4. DJANGO → UTILISATEUR
   - Réponse HTML/JSON
   - Notifications temps réel
   - Mises à jour d'interface
```

---

## 📋 CONCLUSION

### Points clés de l'architecture
- ✅ **Scalable** : Architecture modulaire et extensible
- ✅ **Sécurisée** : Multiples couches de sécurité
- ✅ **Performante** : Optimisation à tous les niveaux
- ✅ **Maintenable** : Code structuré et documenté
- ✅ **Résiliente** : Gestion des erreurs et monitoring

### Technologies principales
- **Backend** : Django 5.2.8 + PostgreSQL + Redis
- **Frontend** : Bootstrap 5 + JavaScript vanilla
- **Infrastructure** : Docker + Nginx + Gunicorn
- **Services** : Orange Money API + MTN API + SMTP

Cette architecture assure une plateforme robuste, sécurisée et performante pour l'e-learning CRVS. 🎯

---

*Document créé le : 16/02/2026*
*Dernière mise à jour : 16/02/2026*
*Version : 1.0*
