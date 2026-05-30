from django.utils import timezone
from .models import ActivityLog, CourseReminder
import logging

logger = logging.getLogger(__name__)

class ActivityTrackingMiddleware:
    """
    Middleware pour enregistrer les activités des utilisateurs.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        # Une réponse par requête
        self._requests = {}

    def __call__(self, request):
        # Vérifier si c'est une requête de connexion ou déconnexion
        if request.path == '/users/login/' and request.method == 'POST':
            # Stocker la requête pour traitement après authentification
            self._requests[id(request)] = request
            request._activity_tracking_middleware = self
        
        # Obtenir la réponse
        response = self.get_response(request)
        
        # Nettoyer
        if id(request) in self._requests:
            del self._requests[id(request)]
            
        return response
    
    @staticmethod
    def get_client_ip(request):
        """Récupère l'adresse IP du client."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def log_activity(self, user, action, request):
        """Enregistre une activité."""
        try:
            ActivityLog.objects.create(
                user=user,
                action=action,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:200],
                timestamp=timezone.now()
            )
            logger.info(f"Activité enregistrée: {user.username} - {action}")
            
            # Si c'est une connexion, vérifier les rappels de cours
            if action == 'login':
                self.check_course_reminders(user)
                
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement de l'activité: {str(e)}")
    
    def check_course_reminders(self, user):
        """
        Vérifie et met à jour les rappels de cours inachevés pour un utilisateur qui se connecte
        """
        try:
            from courses.models import Course
            from django.db.models import Q
            
            # Récupérer tous les cours où l'utilisateur a une progression inachevée
            from .models import LearnerProgress
            incomplete_progress = LearnerProgress.objects.filter(
                user=user,
                completion_percentage__lt=100,
                completion_percentage__gt=0  # Seulement les cours commencés
            ).select_related('course')
            
            for progress in incomplete_progress:
                # Créer ou mettre à jour le rappel
                CourseReminder.update_or_create_reminder(
                    user=user,
                    course=progress.course
                )
                
                logger.info(f"Rappel créé/mis à jour pour {user.username} - {progress.course.title}")
                
        except Exception as e:
            logger.error(f"Erreur lors de la vérification des rappels pour {user.username}: {str(e)}")


class CourseReminderMiddleware:
    """
    Middleware pour gérer les rappels de cours lors de la navigation
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Traitement avant la réponse
        if request.user.is_authenticated:
            self.track_course_activity(request)
        
        response = self.get_response(request)
        
        return response
    
    def track_course_activity(self, request):
        """
        Suit l'activité de l'utilisateur dans les cours pour mettre à jour les rappels
        """
        try:
            # Détecter si l'utilisateur consulte une leçon ou un cours
            if '/courses/course/' in request.path or '/courses/lesson/' in request.path:
                # Extraire l'ID du cours de l'URL
                path_parts = request.path.strip('/').split('/')
                if 'course' in path_parts:
                    course_index = path_parts.index('course')
                    if course_index + 1 < len(path_parts):
                        try:
                            course_id = int(path_parts[course_index + 1])
                            from courses.models import Course
                            course = Course.objects.get(id=course_id)
                            
                            # Mettre à jour le rappel pour ce cours
                            CourseReminder.update_or_create_reminder(
                                user=request.user,
                                course=course
                            )
                            
                            logger.debug(f"Rappel mis à jour pour {request.user.username} - cours {course_id}")
                        except (ValueError, Course.DoesNotExist):
                            pass
                            
        except Exception as e:
            logger.error(f"Erreur lors du suivi d'activité de cours: {str(e)}")
