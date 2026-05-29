from django.core.management.base import BaseCommand
from courses.models import LearningPathTemplate, LearningPath, Course
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Configurer le système scalable de templates et certification'

    def handle(self, *args, **options):
        print("🚀 CONFIGURATION SCALABLE DU SYSTÈME DE TEMPLATES")
        
        # ÉTAPE 1: Créer les templates standards par structure
        self.create_standard_templates()
        
        # ÉTAPE 2: Corriger les utilisateurs existants (comme sango ku)
        self.fix_existing_users()
        
        print("\n✅ Système scalable configuré avec succès !")

    def create_standard_templates(self):
        """Créer les templates standards pour chaque structure"""
        print("\n📋 CRÉATION DES TEMPLATES STANDARDS")
        
        # Récupérer tous les cours disponibles
        all_courses = Course.objects.all()
        if not all_courses.exists():
            print("❌ Aucun cours trouvé. Créez d'abord les cours.")
            return
        
        # Templates standards par structure
        templates_config = {
            'commune': {
                'name': 'Parcours Agent Communal',
                'level': 'beginner',
                'description': 'Parcours complet pour les agents des mairies et communes',
                'sequence': {
                    'certification_required': True,
                    'threshold': 80,
                    'auto_generate': True,
                    'notification_on_completion': True,
                    'certificate_template': 'commune_official'
                }
            },
            'minsante': {
                'name': 'Parcours Personnel Ministériel',
                'level': 'intermediate',
                'description': 'Parcours avancé pour le personnel du Ministère de la Santé',
                'sequence': {
                    'certification_required': True,
                    'threshold': 90,
                    'auto_generate': True,
                    'notification_on_completion': True,
                    'certificate_template': 'minsante_official'
                }
            },
            'bunec': {
                'name': 'Parcours Certifié BUNEC',
                'level': 'advanced',
                'description': 'Parcours expert pour la certification BUNEC',
                'sequence': {
                    'certification_required': True,
                    'threshold': 95,
                    'auto_generate': True,
                    'notification_on_completion': True,
                    'certificate_template': 'bunec_official'
                }
            },
            'multi_structure': {
                'name': 'Parcours Multi-Structures',
                'level': 'beginner',
                'description': 'Parcours par défaut pour toutes les structures',
                'sequence': {
                    'certification_required': True,
                    'threshold': 80,
                    'auto_generate': True,
                    'notification_on_completion': True,
                    'certificate_template': 'default'
                }
            }
        }
        
        created_count = 0
        for structure, config in templates_config.items():
            try:
                template, created = LearningPathTemplate.objects.get_or_create(
                    structure=structure,
                    name=config['name'],
                    defaults={
                        'level': config['level'],
                        'description': config['description'],
                        'estimated_duration': '40:00:00',
                        'sequence': config['sequence'],
                        'is_active': True
                    }
                )
                
                # Assigner tous les cours au template
                template.courses.set(all_courses)
                
                if created:
                    print(f"✅ Template créé: {config['name']} ({structure})")
                    created_count += 1
                else:
                    print(f"⚠️  Template existe déjà: {config['name']} ({structure})")
                    # Mettre à jour la séquence pour activer la certification
                    template.sequence = config['sequence']
                    template.save()
                    print(f"🔄 Template mis à jour: {config['name']}")
                
            except Exception as e:
                print(f"❌ Erreur création template {structure}: {e}")
        
        print(f"📊 Templates traités: {created_count} nouveaux, {len(templates_config) - created_count} existants")

    def fix_existing_users(self):
        """Corriger les utilisateurs existants sans template"""
        print("\n🔧 CORRECTION DES UTILISATEURS EXISTANTS")
        
        # Récupérer tous les utilisateurs avec un LearningPath mais sans template
        users_without_template = User.objects.filter(
            learning_path__template__isnull=True
        ).distinct()
        
        print(f"👤 Utilisateurs sans template: {users_without_template.count()}")
        
        for user in users_without_template:
            try:
                learning_path = user.learning_path
                
                # Chercher le template approprié selon la structure
                template = None
                user_structure = getattr(user, 'structure', None)
                
                if user_structure:
                    template = LearningPathTemplate.objects.filter(
                        structure=user_structure,
                        is_active=True
                    ).first()
                
                # Si pas de template spécifique, utiliser le multi-structures
                if not template:
                    template = LearningPathTemplate.objects.filter(
                        structure='multi_structure',
                        is_active=True
                    ).first()
                
                if template:
                    # Assigner le template
                    learning_path.template = template
                    learning_path.save()
                    
                    print(f"✅ Template '{template.name}' assigné à {user.username}")
                    
                    # Vérifier si l'utilisateur est éligible à la certification
                    self.check_certification_eligibility(user, learning_path, template)
                    
                else:
                    print(f"❌ Aucun template trouvé pour {user.username}")
                    
            except Exception as e:
                print(f"❌ Erreur correction utilisateur {user.username}: {e}")
        
        # Cas spécifique: sango ku
        try:
            sango_ku = User.objects.get(username='sango ku')
            learning_path = sango_ku.learning_path
            
            if not learning_path.template:
                # Assigner le template commune (structure la plus probable)
                template = LearningPathTemplate.objects.filter(
                    structure='commune',
                    is_active=True
                ).first()
                
                if template:
                    learning_path.template = template
                    learning_path.save()
                    
                    print(f"✅ Template 'commune' assigné à sango ku")
                    
                    # Vérifier immédiatement la certification
                    self.check_certification_eligibility(sango_ku, learning_path, template)
                else:
                    print(f"❌ Template 'commune' non trouvé pour sango ku")
            else:
                print(f"ℹ️ sango ku a déjà un template: {learning_path.template.name}")
                
        except User.DoesNotExist:
            print("⚠️  Utilisateur 'sango ku' non trouvé")
        except Exception as e:
            print(f"❌ Erreur traitement sango ku: {e}")

    def check_certification_eligibility(self, user, learning_path, template):
        """Vérifier et générer la certification si éligible"""
        try:
            from certifications.utils import check_certification_eligibility, generate_automatic_certification
            
            eligibility, message = check_certification_eligibility(user, learning_path)
            
            if eligibility:
                certification, result_message = generate_automatic_certification(
                    user, learning_path, template
                )
                
                if certification:
                    print(f"🎓 Certification générée pour {user.username}: {certification.title}")
                    
                    # Envoyer notification
                    from notifications.models import Notification
                    Notification.objects.create(
                        user=user,
                        sender="Système CRVS",
                        subject="🎓 Félicitations ! Certification obtenue",
                        message=f"""
Félicitations {user.get_full_name() or user.username} !

Vous avez obtenu votre certification :
📜 {certification.title}
🎯 Niveau : {certification.get_level_display()}
📅 Date : {certification.issued_at.strftime('%d/%m/%Y')}
🔗 Code : {certification.code}

Votre certificat est disponible dans votre espace personnel.

Bravo pour votre excellent travail !

L'équipe CRVS Learning
                        """.strip(),
                        is_read=False
                    )
                else:
                    print(f"⚠️  Erreur génération certification: {result_message}")
            else:
                print(f"📊 Non éligible à la certification: {message}")
                
        except ImportError:
            print("⚠️ Module certifications non disponible")
        except Exception as e:
            print(f"❌ Erreur vérification certification: {e}")
