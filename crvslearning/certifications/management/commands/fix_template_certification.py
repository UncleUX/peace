from django.core.management.base import BaseCommand
from courses.models import LearningPathTemplate, LearningPath
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Activer la certification dans les templates et vérifier les utilisateurs'

    def add_arguments(self, parser):
        parser.add_argument('--template-name', type=str, help='Nom du template à corriger')
        parser.add_argument('--username', type=str, help='Nom d\'utilisateur spécifique à vérifier')

    def handle(self, *args, **options):
        print("🔧 CORRECTION DES TEMPLATES POUR CERTIFICATION")
        print("=" * 50)
        
        template_name = options.get('template_name')
        username = options.get('username')
        
        # Corriger tous les templates ou un spécifique
        if template_name:
            self.fix_specific_template(template_name)
        else:
            self.fix_all_templates()
        
        # Vérifier un utilisateur spécifique ou tous ceux sans certificat
        if username:
            self.check_user_certification(username)
        else:
            self.check_all_users_without_certification()

    def fix_all_templates(self):
        """Activer la certification dans tous les templates"""
        print("\n🔧 ACTIVATION DE LA CERTIFICATION DANS TOUS LES TEMPLATES")
        
        templates = LearningPathTemplate.objects.all()
        print(f"📋 Templates trouvés: {templates.count()}")
        
        fixed_count = 0
        for template in templates:
            if self.fix_template_certification(template):
                fixed_count += 1
        
        print(f"\n✅ Templates corrigés: {fixed_count}")

    def fix_specific_template(self, template_name):
        """Corriger un template spécifique"""
        print(f"\n🔧 RECHERCHE DU TEMPLATE: {template_name}")
        
        try:
            template = LearningPathTemplate.objects.get(name__icontains=template_name)
            self.fix_template_certification(template)
        except LearningPathTemplate.DoesNotExist:
            print(f"❌ Template '{template_name}' non trouvé")
            
            # Chercher des templates similaires
            similar = LearningPathTemplate.objects.filter(name__icontains=template_name.split()[0])
            if similar.exists():
                print(f"💡 Templates similaires trouvés:")
                for t in similar:
                    print(f"   - {t.name}")
            else:
                print(f"❌ Aucun template similaire trouvé")

    def fix_template_certification(self, template):
        """Activer la certification dans un template"""
        sequence = template.sequence or {}
        
        if not sequence.get('certification_required', False):
            # Activer la certification
            sequence.update({
                'certification_required': True,
                'threshold': 80,
                'auto_generate': True,
                'notification_on_completion': True,
                'certificate_template': 'default'
            })
            
            template.sequence = sequence
            template.save()
            
            print(f"✅ Template '{template.name}' corrigé:")
            print(f"   🎓 Certification requise: True")
            print(f"   📊 Seuil: 80%")
            print(f"   🤖 Auto-génération: True")
            
            return True
        else:
            print(f"⚠️ Template '{template.name}' a déjà la certification activée")
            return False

    def check_all_users_without_certification(self):
        """Vérifier tous les utilisateurs sans certification"""
        print("\n👤 VÉRIFICATION DES UTILISATEURS SANS CERTIFICATION")
        
        from certifications.models import Certification
        
        # Utilisateurs avec un LearningPath mais sans certification
        users_with_path = User.objects.filter(learning_path__isnull=False)
        users_without_cert = users_with_path.exclude(
            id__in=Certification.objects.values('user_id')
        )
        
        print(f"📊 Utilisateurs sans certification: {users_without_cert.count()}")
        
        for user in users_without_cert:
            self.check_user_certification(user.username)

    def check_user_certification(self, username):
        """Vérifier et générer la certification pour un utilisateur"""
        print(f"\n🔍 VÉRIFICATION DE: {username}")
        
        try:
            user = User.objects.get(username=username)
            learning_path = user.learning_path
            
            if not learning_path.template:
                print(f"❌ Aucun template assigné à {username}")
                return
            
            template = learning_path.template
            sequence = template.sequence or {}
            
            if not sequence.get('certification_required', False):
                print(f"❌ Template '{template.name}' n'a pas la certification activée")
                return
            
            # Calculer la progression
            total_courses = template.courses.count()
            completed_courses = learning_path.completed_courses.filter(
                id__in=template.courses.all()
            ).count()
            
            print(f"📊 Progression: {completed_courses}/{total_courses} ({(completed_courses/total_courses*100):.1f}%)")
            
            if completed_courses >= total_courses:
                print(f"✅ PARCOURS TERMINÉ - Génération du certificat...")
                self.generate_certification(user, learning_path, template)
            else:
                print(f"⏳ Parcours non terminé - manque {total_courses - completed_courses} cours")
                
        except User.DoesNotExist:
            print(f"❌ Utilisateur '{username}' non trouvé")
        except Exception as e:
            print(f"❌ Erreur: {e}")

    def generate_certification(self, user, learning_path, template):
        """Générer la certification"""
        try:
            from certifications.utils import generate_automatic_certification
            
            certification, result_message = generate_automatic_certification(
                user, learning_path.template
            )
            
            if certification:
                print(f"🎓 CERTIFICAT GÉNÉRÉ: {certification.title}")
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
                
                print(f"📬 Notification envoyée à {user.username}")
                print(f"🎉 Problème résolu pour {user.username}!")
                
            else:
                print(f"❌ Erreur génération certification: {result_message}")
                
        except Exception as e:
            print(f"❌ Erreur: {e}")
