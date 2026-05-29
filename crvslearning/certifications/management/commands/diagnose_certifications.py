from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from courses.models import LearningPath, CourseCompletion
from certifications.models import Certification

User = get_user_model()

class Command(BaseCommand):
    help = 'Diagnostiquer pourquoi un utilisateur n\'a pas reçu de certification'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Nom d\'utilisateur à diagnostiquer')

    def handle(self, *args, **options):
        username = options['username']
        
        try:
            user = User.objects.get(username=username)
            print(f"\n🔍 DIAGNOSTIC POUR L'UTILISATEUR: {username}")
            print(f"📧 Email: {user.email}")
            print(f"📧 Rôle: {user.role}")
            
            # Vérifier le LearningPath
            try:
                learning_path = LearningPath.objects.get(user=user)
                if learning_path.template:
                    print(f"\n✅ LearningPath trouvé: {learning_path.template.name}")
                    print(f"📊 Template ID: {learning_path.template.id}")
                    print(f"📊 Cours dans template: {learning_path.template.courses.count()}")
                    print(f"📊 Cours complétés: {learning_path.completed_courses.count()}")
                    print(f"📊 Cours requis: {learning_path.template.courses.count()}")
                    print(f"📊 Pourcentage: {(learning_path.completed_courses.count() / learning_path.template.courses.count() * 100):.1f}%")
                    print(f"📊 Certification obtenue: {learning_path.certification_obtained}")
                else:
                    print(f"\n❌ LearningPath trouvé mais SANS template")
                    print(f"📊 Cours complétés: {learning_path.completed_courses.count()}")
                    print(f"📊 Certification obtenue: {learning_path.certification_obtained}")
                
                # Vérifier les complétions de cours
                if learning_path.template:
                    completions = CourseCompletion.objects.filter(
                        user=user,
                        course__in=learning_path.template.courses.all()
                    )
                    print(f"\n📊 Complétions de cours trouvées: {completions.count()}")
                    
                    for completion in completions:
                        print(f"   📚 Cours: {completion.course.title}")
                        print(f"   📅 Complété le: {completion.completed_at}")
                        print(f"   📊 Score: {completion.score}/{completion.max_score}")
                else:
                    completions = CourseCompletion.objects.filter(user=user)
                    print(f"\n📊 Complétions de cours trouvées (sans template): {completions.count()}")
                    
                    for completion in completions:
                        print(f"   📚 Cours: {completion.course.title}")
                        print(f"   📅 Complété le: {completion.completed_at}")
                
                # Vérifier l'éligibilité à la certification
                if learning_path.template:
                    total_courses = learning_path.template.courses.count()
                    completed_courses = learning_path.completed_courses.filter(
                        id__in=learning_path.template.courses.all()
                    ).count()
                    
                    print(f"\n📊 Éligibilité certification:")
                    print(f"   📚 Total cours: {total_courses}")
                    print(f"   📚 Cours complétés: {completed_courses}")
                    print(f"   📊 Pourcentage: {(completed_courses / total_courses * 100):.1f}%")
                    
                    if completed_courses >= total_courses:
                        print(f"   ✅ ÉLIGIBLE à la certification")
                    else:
                        print(f"   ❌ NON ÉLIGIBLE - il manque {total_courses - completed_courses} cours")
                else:
                    print(f"\n❌ Aucun template trouvé pour le LearningPath")
                    
            except LearningPath.DoesNotExist:
                print(f"\n❌ Aucun LearningPath trouvé pour {username}")
            
            # Vérifier les certifications existantes
            certifications = Certification.objects.filter(user=user)
            print(f"\n📜 Certifications existantes: {certifications.count()}")
            
            for cert in certifications:
                print(f"   🎓 {cert.level.upper()}: {cert.title}")
                print(f"   📅 Code: {cert.code}")
                print(f"   📅 Cours: {cert.course.title}")
                print(f"   📅 Délivré le: {cert.issued_at}")
                print(f"   📅 Valide: {cert.is_valid}")
                print(f"   📅 PDF: {'Oui' if cert.pdf else 'Non'}")
            
            # Vérifier les dernières activités
            from notifications.models import Notification
            recent_notifications = Notification.objects.filter(
                user=user,
                is_read=False
            ).order_by('-created_at')[:5]
            
            print(f"\n📬 Notifications récentes: {recent_notifications.count()}")
            for notif in recent_notifications:
                print(f"   🔔 {notif.created_at}: {notif.subject[:50]}")
                print(f"   📧 Expéditeur: {notif.sender}")
                print(f"   📄 Lu: {notif.is_read}")
            
            # Vérifier s'il y a eu des problèmes récents
            if certifications.count() == 0 and learning_path:
                print(f"\n⚠️  PROBLÈME DÉTECTÉ:")
                print(f"   ❌ L'utilisateur a un LearningPath mais aucune certification")
                print(f"   ❌ Les signaux de certification ne se sont pas déclenchés")
                print(f"   💡 Solution possible: Vérifier la configuration des signaux")
                
        except User.DoesNotExist:
            print(f"\n❌ Utilisateur {username} non trouvé")
