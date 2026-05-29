"""
Signaux Django pour le système de parcours d'apprentissage
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Count

from .models import LearningPath, LearningPathTemplate, CourseCompletion, LessonProgress

User = get_user_model()


@receiver(post_save, sender=User)
def create_learning_path(sender, instance, created, **kwargs):
    """
    Créer automatiquement un LearningPath pour chaque nouvel utilisateur
    avec assignation automatique du template selon la structure
    """
    if created:
        # Créer le parcours d'apprentissage personnel
        learning_path, created_path = LearningPath.objects.get_or_create(user=instance)
        
        if created_path:
            # Tenter d'assigner un template automatiquement selon la structure
            try:
                template = LearningPathTemplate.objects.get(
                    structure=instance.structure,
                    level='beginner',
                    is_active=True
                )
                learning_path.template = template
                learning_path.save()
                
                print(f"✅ Template '{template.name}' assigné à {instance.username} (structure: {instance.structure})")
                
                # Envoyer notification d'assignation
                from notifications.models import Notification
                Notification.objects.create(
                    user=instance,
                    sender="Système CRVS",
                    subject="Parcours d'apprentissage assigné",
                    message=f"""
Bonjour {instance.get_full_name() or instance.username},

Votre parcours d'apprentissage a été automatiquement configuré selon votre structure ({instance.structure}).

📚 Parcours assigné : {template.name}
🎯 Niveau : {template.get_level_display()}
📊 Cours inclus : {template.courses.count()}
⏱️ Durée estimée : {template.estimated_duration}

Vous pouvez commencer votre formation dès maintenant !

Cordialement,
L'équipe CRVS Learning
                    """.strip(),
                    is_read=False
                )
                
            except LearningPathTemplate.DoesNotExist:
                # Si aucun template n'existe pour cette structure,
                # essayer le template multi-structures
                try:
                    default_template = LearningPathTemplate.objects.get(
                        structure='multi_structure',
                        is_active=True
                    )
                    learning_path.template = default_template
                    learning_path.save()
                    
                    print(f"Template par defaut assigne a {instance.username}")
                    
                except LearningPathTemplate.DoesNotExist:
                    # Creer un parcours vide avec des objectifs par defaut
                    default_goals = get_default_goals_by_structure(instance.structure)
                    if default_goals:
                        learning_path.learning_goals = default_goals
                        learning_path.save()
                    
                    print(f"Aucun template trouve pour {instance.structure} - parcours vide cree")
            
            print(f"LearningPath cree pour l'utilisateur {instance.username}")
        else:
            print(f"LearningPath existe deja pour l'utilisateur {instance.username}")


@receiver(post_save, sender=User)
def assign_learning_path_template(sender, instance, created, **kwargs):
    """
    Assigner automatiquement un template de parcours à l'utilisateur
    - Nouveaux utilisateurs: assigner le template de leur structure
    - Utilisateurs existants sans template: assigner le template de leur structure
    - Structure modifiée: réassigner le template de la nouvelle structure
    """
    try:
        # Vérifier si l'utilisateur a déjà un template assigné
        try:
            learning_path = LearningPath.objects.get(user=instance)
            has_template = learning_path.template is not None
        except LearningPath.DoesNotExist:
            learning_path = LearningPath.objects.create(user=instance)
            has_template = False
        
        # Conditions pour l'assignation automatique
        should_assign = (
            created or  # Nouvel utilisateur
            (kwargs.get('update_fields') and 'structure' in kwargs['update_fields']) or  # Structure modifiée
            not has_template  # Pas de template assigné
        )
        
        if should_assign:
            # Récupérer le template approprié pour la structure de l'utilisateur
            # Chercher d'abord dans la structure principale
            template = LearningPathTemplate.objects.filter(
                structure=instance.structure,
                is_active=True
            ).first()
            
            # Si pas trouvé, chercher dans les structures additionnelles
            if not template:
                template = LearningPathTemplate.objects.filter(
                    is_active=True
                ).filter(
                    additional_structures__icontains=instance.structure
                ).first()
            
            if template:
                # Assigner le template à l'utilisateur
                template.assign_to_user(instance)
                
                print(f"Template '{template.name}' assigne a {instance.username} (structure: {instance.get_structure_display()})")
                
                # Envoyer une notification a l'utilisateur
                try:
                    from notifications.models import Notification
                    notification = Notification.objects.create(
                        user=instance,
                        sender="CRVS Learning",
                        subject="Nouveau parcours disponible",
                        message=f"Felicitations ! Un parcours d'apprentissage '{template.name}' a ete assigne a votre profil. Commencez des maintenant votre formation et obtenez votre certification.",
                        url="/courses/learning-path/"
                    )
                    print(f"Notification envoyee a {instance.username}")
                    
                    # Envoyer aussi un email si active
                    if getattr(template, 'enable_email_notifications', False):
                        try:
                            template.send_email_notification(instance)
                            print(f"Email envoye a {instance.email}")
                        except Exception as email_error:
                            print(f"Erreur email: {email_error}")
                            
                except Exception as notif_error:
                    print(f"Erreur notification: {notif_error}")
                    
            else:
                print(f"Aucun template trouve pour la structure '{instance.get_structure_display()}'")
                
    except Exception as e:
        print(f"Erreur lors de l'assignation du template pour {instance.username}: {e}")


# Signal pour assigner automatiquement tous les utilisateurs sans template quand un template est activé
@receiver(post_save, sender=LearningPathTemplate)
def assign_template_to_existing_users(sender, instance, created, **kwargs):
    """
    Quand un template est créé/activé, l'assigner à tous les utilisateurs
    de la structure cible qui n'ont pas encore de template
    """
    if created or (kwargs.get('update_fields') and 'is_active' in kwargs['update_fields']):
        if instance.is_active:
            try:
                # Importer User ici pour éviter les imports circulaires
                from django.contrib.auth import get_user_model
                User = get_user_model()
                
                # Trouver tous les utilisateurs de cette structure sans template
                users_without_template = []
                for user in User.objects.filter(structure=instance.structure):
                    try:
                        lp = LearningPath.objects.get(user=user)
                        if lp.template is None:
                            users_without_template.append(user)
                    except LearningPath.DoesNotExist:
                        users_without_template.append(user)
                
                # Assigner le template à tous ces utilisateurs
                assigned_count = 0
                for user in users_without_template:
                    try:
                        instance.assign_to_user(user)
                        assigned_count += 1
                        print(f"✅ Template '{instance.name}' assigné à {user.username}")
                        
                        # Envoyer une notification à chaque utilisateur
                        try:
                            from notifications.models import Notification
                            notification = Notification.objects.create(
                                user=user,
                                sender="CRVS Learning",
                                subject="🎓 Nouveau parcours disponible",
                                message=f"Félicitations ! Un parcours d'apprentissage '{instance.name}' a été assigné à votre profil. Commencez dès maintenant votre formation et obtenez votre certification.",
                                url="/courses/learning-path/"
                            )
                            print(f"📧 Notification envoyée à {user.username}")
                            
                            # Envoyer aussi un email si activé
                            if getattr(instance, 'enable_email_notifications', False):
                                try:
                                    instance.send_email_notification(user)
                                    print(f"📧 Email envoyé à {user.email}")
                                except Exception as email_error:
                                    print(f"⚠️ Erreur email: {email_error}")
                                    
                        except Exception as notif_error:
                            print(f"⚠️ Erreur notification pour {user.username}: {notif_error}")
                            
                    except Exception as e:
                        print(f"❌ Erreur assignation à {user.username}: {e}")
                
                if assigned_count > 0:
                    print(f"🎯 {assigned_count} utilisateurs de la structure '{instance.get_structure_display()}' ont reçu le template '{instance.name}'")
                else:
                    print(f"ℹ️ Tous les utilisateurs de la structure '{instance.get_structure_display()}' ont déjà un template")
                    
            except Exception as e:
                print(f"❌ Erreur lors de l'assignation massive: {e}")


@receiver(post_save, sender=LearningPathTemplate)
def update_existing_paths_on_template_change(sender, instance, created, **kwargs):
    """
    Mettre à jour les parcours existants quand un template est modifié
    """
    if not created and kwargs.get('update_fields'):
        # Si le template a été modifié, notifier les utilisateurs concernés
        users = instance.get_recommended_users()
        print(f"🔄 Template '{instance.name}' modifié - {users.count()} utilisateurs concernés")


def get_default_goals_by_structure(structure):
    """
    Retourne les objectifs d'apprentissage par défaut selon la structure
    """
    goals_by_structure = {
        'commune': "Devenir un agent d'état civil compétent dans la gestion des actes de naissance, mariage et décès.",
        'minsante': "Maîtriser la gestion des actes de naissance en milieu médical et collaborer avec les autres structures.",
        'bunec': "Développer une expertise dans la supervision et le contrôle qualité des services d'état civil.",
        'universite': "Acquérir des compétences théoriques et pratiques en démographie et statistiques.",
        'ong': "Appliquer les connaissances en état civil dans le contexte des organisations non gouvernementales.",
        'consultant': "Offrir des services spécialisés en état civil aux clients privés et organisations.",
        'partenaire': "Collaborer efficacement avec les partenaires institutionnels dans les projets d'état civil.",
        'autre': "Développer une polyvalence dans les différents aspects de l'état civil.",
        'multi_structure': "Acquérir des compétences inter-structures pour une compréhension globale du système."
    }
    
    return goals_by_structure.get(structure, "Développer ses compétences en état civil.")


@receiver(post_save, sender=LearningPath)
def trigger_certification_check(sender, instance, created, **kwargs):
    """
    Déclencher la vérification de certification automatiquement
    """
    if created:
        return  # Pas de vérification pour les nouveaux LearningPaths
    
    # Vérifier si le template est assigné et la certification est requise
    if not instance.template:
        return
    
    template = instance.template
    
    # NOUVELLE APPROCHE: Utiliser les champs directs du modèle
    if not template.certification_required:
        return  # Certification non activée dans ce template
    
    # Importer ici pour éviter les imports circulaires
    try:
        from certifications.utils import check_certification_eligibility, generate_automatic_certification
        
        # Calculer la progression
        total_courses = template.courses.count()
        completed_courses = instance.completed_courses.filter(
            id__in=template.courses.all()
        ).count()
        
        if total_courses > 0:
            progress_percentage = (completed_courses / total_courses) * 100
            
            # Vérifier si le seuil est atteint
            if progress_percentage >= template.certification_threshold:
                # Vérifier l'éligibilité complète
                eligibility, message = check_certification_eligibility(instance.user, instance)
                
                if eligibility and template.auto_generate_certification:
                    certification, result_message = generate_automatic_certification(
                        instance.user,
                        instance,
                        template
                    )
                    
                    if certification:
                        print(f"🎓 Certification automatique générée pour {instance.user.username}")
                        
                        # Envoyer notification de certification
                        from notifications.models import Notification
                        Notification.objects.create(
                            user=instance.user,
                            sender="Système CRVS",
                            subject="🎓 Félicitations ! Certification obtenue",
                            message=f"""
Félicitations {instance.user.get_full_name() or instance.user.username} !

Vous avez obtenu votre certification :
📜 {certification.title}
🎯 Niveau : {template.get_certification_level_display() or template.certification_level}
📅 Date : {certification.issued_at.strftime('%d/%m/%Y')}
🔗 Code : {certification.code}
📊 Progression : {progress_percentage:.1f}%

Votre certificat est disponible dans votre espace personnel.

Bravo pour votre excellent travail !

L'équipe CRVS Learning
                            """.strip(),
                            is_read=False
                        )
                        
                        # Mettre à jour le LearningPath
                        instance.certification_obtained = True
                        instance.certification_date = certification.issued_at
                        instance.save(update_fields=['certification_obtained', 'certification_date'])
                        
                    else:
                        print(f"⚠️  Erreur génération certification: {result_message}")
                else:
                    print(f"📊 Seuil atteint mais non éligible: {message}")
            else:
                print(f"📊 Progression {progress_percentage:.1f}% < seuil {template.certification_threshold}%")
    
    except ImportError:
        print("⚠️ Module certifications non disponible")
    except Exception as e:
        print(f"❌ Erreur vérification certification: {e}")


@receiver(post_save, sender=LearningPath)
def track_learning_path_activity(sender, instance, created, **kwargs):
    """
    Suivre l'activité du parcours d'apprentissage pour les statistiques
    """
    if not created and kwargs.get('update_fields'):
        # Si le parcours a été mis à jour, enregistrer l'activité
        if 'last_activity' in kwargs['update_fields']:
            print(f"📊 Activité enregistrée pour {instance.user.username} à {instance.last_activity}")


@receiver(post_save, sender=User)
def welcome_new_user_with_learning_path(sender, instance, created, **kwargs):
    """
    Envoyer un message de bienvenue avec informations sur le parcours
    """
    if created:
        try:
            learning_path = instance.learning_path
            
            if learning_path.current_course:
                message = f"🎓 Bienvenue sur CRVS Learning, {instance.get_full_name or instance.username} !\n\nVotre parcours d'apprentissage a été configuré :\n📚 Cours actuel : {learning_path.current_course.title}\n🎯 Objectifs : {learning_path.learning_goals or 'Personnalisés selon votre profil'}\n\nCommencez dès maintenant votre formation !"
            else:
                message = f"🎓 Bienvenue sur CRVS Learning, {instance.get_full_name or instance.username} !\n\nVotre parcours d'apprentissage a été créé.\n🎯 Objectifs : {learning_path.learning_goals or 'Personnalisés selon votre profil'}\n\nChoisissez votre parcours pour commencer votre formation !"
            
            print(f"📧 Message de bienvenue généré pour {instance.username}")
            
        except Exception as e:
            print(f"⚠️ Erreur lors de la génération du message de bienvenue : {e}")


@receiver(post_save, sender=CourseCompletion)
def update_learning_path_on_course_completion(sender, instance, created, **kwargs):
    """
    Mettre à jour automatiquement le LearningPath quand un cours est terminé
    """
    if created:
        try:
            learning_path = instance.user.learning_path
            
            # Ajouter le cours aux cours complétés du parcours
            learning_path.completed_courses.add(instance.course)
            
            # Mettre à jour le cours suivant automatiquement
            if learning_path.current_course == instance.course:
                # Utiliser la nouvelle méthode pour trouver le cours suivant
                next_course = instance.course.get_next_course(instance.user.structure)
                
                if next_course:
                    learning_path.current_course = next_course
                    print(f"✅ Passage automatique au cours suivant: {next_course.title}")
                else:
                    learning_path.current_course = None  # Plus de cours disponibles
                    print(f"🎉 Tous les cours terminés pour {instance.user.username}")
                
                learning_path.save()
            
            print(f"✅ Cours '{instance.course.title}' ajouté au parcours de {instance.user.username}")
            
            # Vérifier si tous les cours sont terminés pour la certification
            if learning_path.template:
                total_courses = learning_path.template.courses.count()
                completed_courses = learning_path.completed_courses.filter(id__in=learning_path.template.courses.all()).count()
                completion_rate = completed_courses / total_courses * 100 if total_courses > 0 else 0
                
                # Vérifier si le seuil de certification est atteint
                if completion_rate >= learning_path.template.certification_threshold:
                    # Vérifier si la certification existe déjà pour éviter les doublons
                    from certifications.models import Certification
                    existing_cert = Certification.objects.filter(
                        user=instance.user,
                        template=learning_path.template
                    ).exists()
                    
                    if not existing_cert:
                        # Générer la certification automatiquement
                        from certifications.utils import generate_automatic_certification
                        cert, message = generate_automatic_certification(instance.user, learning_path.template)
                        if cert:
                            print(f"🎓 Certification générée automatiquement: {cert.code}")
                            
                            # Envoyer une notification unique
                            try:
                                from notifications.models import Notification
                                notification, created = Notification.objects.get_or_create(
                                    user=instance.user,
                                    subject="🎓 Félicitations ! Certification obtenue",
                                    defaults={
                                        'sender': "CRVS Learning",
                                        'message': f"Félicitations ! Vous avez obtenu votre certification '{cert.title}'. Téléchargez votre certificat dès maintenant.",
                                        'url': f"/certifications/download/{cert.code}/"
                                    }
                                )
                                if created:
                                    print(f"📧 Notification de certification envoyée à {instance.user.username}")
                            except Exception as notif_error:
                                print(f"⚠️ Erreur notification certification: {notif_error}")
                        else:
                            print(f"ℹ️ Certification non générée: {message}")
                    else:
                        print(f"ℹ️ Certification déjà existante pour {instance.user.username}")
            
            # Envoyer un message de succès (sera affiché à la prochaine requête)
            from django.contrib import messages
            # Note: Les messages ne peuvent pas être ajoutés directement dans les signaux
            # car il n'y a pas de contexte de requête. La redirection sera gérée dans la vue.
            
        except Exception as e:
            print(f"❌ Erreur mise à jour LearningPath: {e}")


@receiver(post_delete, sender=CourseCompletion)
def remove_course_from_learning_path(sender, instance, **kwargs):
    """
    Retirer un cours du LearningPath quand il est supprimé
    """
    try:
        learning_path = instance.user.learning_path
        learning_path.completed_courses.remove(instance.course)
        
        print(f"🗑️ Cours '{instance.course.title}' retiré du parcours de {instance.user.username}")
        
    except Exception as e:
        print(f"❌ Erreur retrait cours LearningPath: {e}")


@receiver(post_save, sender=LessonProgress)
def update_course_completion_on_lesson_progress(sender, instance, created, **kwargs):
    """
    Mettre à jour CourseCompletion quand une leçon est marquée comme terminée
    """
    if instance.is_completed:
        try:
            course = instance.lesson.module.course
            
            # Vérifier si toutes les leçons du cours sont terminées
            total_lessons = course.modules.aggregate(
                total=Count('lessons')
            )['total'] or 0
            
            completed_lessons = course.modules.filter(
                lessons__lessonprogress__user=instance.user,
                lessons__lessonprogress__is_completed=True
            ).aggregate(
                completed=Count('lessons')
            )['completed'] or 0
            
            # Si toutes les leçons sont terminées, créer CourseCompletion
            if total_lessons > 0 and completed_lessons >= total_lessons:
                CourseCompletion.objects.get_or_create(
                    user=instance.user,
                    course=course,
                    defaults={'completed_at': timezone.now()}
                )
                print(f"✅ CourseCompletion créé pour '{course.title}' - {instance.user.username}")
            
        except Exception as e:
            print(f"❌ Erreur mise à jour CourseCompletion: {e}")
