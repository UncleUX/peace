from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from courses.models import LearningPath
from certifications.models import Certification

User = get_user_model()

class Command(BaseCommand):
    help = 'Vérifier et résoudre les problèmes de certification pour un utilisateur'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Nom d\'utilisateur à vérifier')

    def handle(self, *args, **options):
        username = options['username']
        
        print(f"🔍 VÉRIFICATION COMPLÈTE POUR: {username}")
        print("=" * 50)
        
        try:
            user = User.objects.get(username=username)
            print(f"✅ Utilisateur trouvé: {user.get_full_name() or user.username}")
            print(f"📧 Email: {user.email}")
            print(f"🏢 Structure: {getattr(user, 'structure', 'Non définie')}")
            
            # Vérifier les certificats existants
            certifications = Certification.objects.filter(user=user)
            print(f"\n📜 CERTIFICATIONS EXISTANTES: {certifications.count()}")
            
            for cert in certifications:
                print(f"   🎓 {cert.title}")
                print(f"   🎯 Niveau: {cert.get_level_display()}")
                print(f"   📅 Date: {cert.issued_at.strftime('%d/%m/%Y %H:%M')}")
                print(f"   🔗 Code: {cert.code}")
                print(f"   ✅ Valide: {cert.is_valid}")
                print(f"   📄 PDF: {'Oui' if cert.pdf else 'Non'}")
                print("   " + "-" * 40)
            
            if certifications.exists():
                print(f"\n✅ L'utilisateur a déjà {certifications.count()} certificat(s)!")
                return
            
            # Si aucun certificat, vérifier le LearningPath
            print(f"\n📊 ANALYSE DU LEARNINGPATH")
            
            try:
                learning_path = LearningPath.objects.get(user=user)
                print(f"✅ LearningPath trouvé")
                
                if learning_path.template:
                    template = learning_path.template
                    print(f"🎯 Template: {template.name}")
                    print(f"📊 Structure template: {template.structure}")
                    print(f"🎯 Niveau template: {template.level}")
                    print(f"📋 Configuration: {template.sequence}")
                    
                    # Vérifier si la certification est requise
                    sequence = template.sequence or {}
                    cert_required = sequence.get('certification_required', False)
                    threshold = sequence.get('threshold', 80)
                    
                    print(f"🎓 Certification requise: {cert_required}")
                    print(f"📊 Seuil requis: {threshold}%")
                    
                    if not cert_required:
                        print(f"❌ PROBLÈME: La certification n'est PAS activée dans ce template!")
                        self.fix_template_certification(template)
                    
                    # Calculer la progression
                    total_courses = template.courses.count()
                    completed_courses = learning_path.completed_courses.filter(
                        id__in=template.courses.all()
                    ).count()
                    
                    print(f"\n📊 PROGRESSION:")
                    print(f"📚 Total cours: {total_courses}")
                    print(f"✅ Cours complétés: {completed_courses}")
                    
                    if total_courses > 0:
                        progress_percentage = (completed_courses / total_courses) * 100
                        print(f"📊 Pourcentage: {progress_percentage:.1f}%")
                        
                        if completed_courses >= total_courses:
                            print(f"✅ PARCOURS TERMINÉ - Devrait avoir une certification!")
                            self.generate_missing_certification(user, learning_path, template)
                        else:
                            print(f"⏳ Parcours non terminé - manque {total_courses - completed_courses} cours")
                    else:
                        print(f"❌ Aucun cours dans ce template!")
                    
                else:
                    print(f"❌ PROBLÈME: Aucun template assigné!")
                    self.assign_template_to_user(user, learning_path)
                    
            except LearningPath.DoesNotExist:
                print(f"❌ PROBLÈME: Aucun LearningPath trouvé!")
                self.create_learning_path_for_user(user)
                
        except User.DoesNotExist:
            print(f"❌ Utilisateur '{username}' non trouvé")

    def fix_template_certification(self, template):
        """Activer la certification dans le template"""
        print(f"\n🔧 CORRECTION DU TEMPLATE")
        
        sequence = template.sequence or {}
        sequence.update({
            'certification_required': True,
            'threshold': 80,
            'auto_generate': True,
            'notification_on_completion': True
        })
        
        template.sequence = sequence
        template.save()
        
        print(f"✅ Template '{template.name}' corrigé - Certification activée!")

    def assign_template_to_user(self, user, learning_path):
        """Assigner un template approprié à l'utilisateur"""
        print(f"\n🔧 ASSIGNATION D'UN TEMPLATE")
        
        from courses.models import LearningPathTemplate
        
        # Chercher le template selon la structure
        user_structure = getattr(user, 'structure', None)
        template = None
        
        if user_structure:
            template = LearningPathTemplate.objects.filter(
                structure=user_structure,
                is_active=True
            ).first()
        
        # Fallback sur multi-structures
        if not template:
            template = LearningPathTemplate.objects.filter(
                structure='multi_structure',
                is_active=True
            ).first()
        
        if template:
            learning_path.template = template
            learning_path.save()
            
            print(f"✅ Template '{template.name}' assigné à {user.username}")
            
            # Vérifier immédiatement la certification
            self.check_and_generate_certification(user, learning_path, template)
        else:
            print(f"❌ Aucun template disponible pour {user.username}")

    def create_learning_path_for_user(self, user):
        """Créer un LearningPath pour l'utilisateur"""
        print(f"\n🔧 CRÉATION DU LEARNINGPATH")
        
        from courses.models import LearningPathTemplate
        
        learning_path = LearningPath.objects.create(user=user)
        
        # Assigner un template
        user_structure = getattr(user, 'structure', None)
        template = None
        
        if user_structure:
            template = LearningPathTemplate.objects.filter(
                structure=user_structure,
                is_active=True
            ).first()
        
        if not template:
            template = LearningPathTemplate.objects.filter(
                structure='multi_structure',
                is_active=True
            ).first()
        
        if template:
            learning_path.template = template
            learning_path.save()
            
            print(f"✅ LearningPath créé avec template '{template.name}'")
            self.check_and_generate_certification(user, learning_path, template)
        else:
            print(f"❌ LearningPath créé mais aucun template disponible")

    def check_and_generate_certification(self, user, learning_path, template):
        """Vérifier et générer la certification"""
        try:
            from certifications.utils import check_certification_eligibility, generate_automatic_certification
            
            eligibility, message = check_certification_eligibility(user, learning_path)
            
            if eligibility:
                certification, result_message = generate_automatic_certification(
                    user, template
                )
                
                if certification:
                    print(f"🎓 CERTIFICAT GÉNÉRÉ: {certification.title}")
                    print(f"🔗 Code: {certification.code}")
                    print(f"📅 Date: {certification.issued_at}")
                    
                    # Envoyer notification
                    from notifications.models import Notification
                    Notification.objects.create(
                        user=user,
                        sender="Système CRVS",
                        subject="🎓 Félicitations ! Certification obtenue",
                        message=f"""
Félicitations {user.get_full_name() or user.username} !

Votre certification a été générée :
📜 {certification.title}
🎯 Niveau : {certification.get_level_display()}
📅 Date : {certification.issued_at.strftime('%d/%m/%Y')}
🔗 Code : {certification.code}

Votre certificat est disponible dans votre espace personnel.

L'équipe CRVS Learning
                        """.strip(),
                        is_read=False
                    )
                    print(f"📬 Notification envoyée à {user.username}")
                else:
                    print(f"❌ Erreur génération: {result_message}")
            else:
                print(f"📊 Non éligible: {message}")
                
        except Exception as e:
            print(f"❌ Erreur vérification certification: {e}")

    def generate_missing_certification(self, user, learning_path, template):
        """Générer la certification manquante"""
        print(f"\n🎓 GÉNÉRATION DE LA CERTIFICATION MANQUANTE")
        
        try:
            from certifications.utils import generate_automatic_certification
            
            certification, result_message = generate_automatic_certification(
                user, template
            )
            
            if certification:
                print(f"✅ CERTIFICAT CRÉÉ: {certification.title}")
                print(f"🔗 Code: {certification.code}")
                print(f"📅 Date: {certification.issued_at}")
                
                # Mettre à jour le LearningPath
                learning_path.certification_obtained = True
                learning_path.certification_date = certification.issued_at
                learning_path.save()
                
                # Envoyer notification
                from notifications.models import Notification
                Notification.objects.create(
                    user=user,
                    sender="Système CRVS",
                    subject="🎓 Félicitations ! Certification obtenue",
                    message=f"""
Félicitations {user.get_full_name() or user.username} !

Votre certification a été générée automatiquement :
📜 {certification.title}
🎯 Niveau : {certification.get_level_display()}
📅 Date : {certification.issued_at.strftime('%d/%m/%Y')}
🔗 Code : {certification.code}

Votre certificat est maintenant disponible dans votre espace personnel.

Bravo pour votre excellent travail !

L'équipe CRVS Learning
                    """.strip(),
                    is_read=False
                )
                
                print(f"📬 Notification de certification envoyée")
                print(f"🎉 Problème résolu pour {user.username}!")
                
            else:
                print(f"❌ Erreur génération certification: {result_message}")
                
        except Exception as e:
            print(f"❌ Erreur: {e}")
