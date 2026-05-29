"""
Utilitaires pour la gestion des parcours d'apprentissage
"""

from django.contrib.auth import get_user_model
from .models import LearningPath, Course, Module, Lesson, LessonProgress, Enrollment
from django.utils import timezone

User = get_user_model()

def can_access_course(user, course):
    """
    Vérifie si un utilisateur peut accéder à un cours
    Prend en compte les inscriptions ET les prérequis
    """
    # Vérifier si l'utilisateur est inscrit au cours
    if not Enrollment.objects.filter(user=user, course=course).exists():
        return False, "Non inscrit"
    
    # Vérifier si le cours est publié
    if not course.is_published:
        return False, "Cours non publié"
    
    # Vérifier les prérequis
    can_access, message = check_course_prerequisites(user, course)
    
    return can_access, message

def check_course_prerequisites(user, course):
    """
    Vérifie si l'utilisateur a complété les prérequis pour un cours
    """
    # Récupérer le module du cours
    try:
        module = Module.objects.get(courses=course)
    except Module.DoesNotExist:
        # Si le cours n'est pas dans un module, pas de prérequis
        return True, "Aucun prérequis"
    
    # Vérifier si c'est le premier module du parcours
    if module.order == 1:
        return True, "Premier module - accessible"
    
    # Récupérer les modules précédents
    previous_modules = Module.objects.filter(
        order__lt=module.order,
        learningpathtemplate__learningpath__user=user
    ).order_by('-order')
    
    # Vérifier si les modules précédents sont complétés
    for prev_module in previous_modules:
        if not is_module_completed(user, prev_module):
            return False, f"Prérequis non complété: {prev_module.name}"
    
    return True, "Prérequis validés"

def is_module_completed(user, module):
    """
    Vérifie si un module est complété pour un utilisateur
    """
    # Compter le nombre de leçons complétées dans le module
    total_lessons = Lesson.objects.filter(module=module).count()
    completed_lessons = LessonProgress.objects.filter(
        user=user,
        lesson__module=module,
        is_fully_completed=True
    ).count()
    
    # Si 80% ou plus des leçons sont complétées, considérer le module comme complété
    if total_lessons > 0 and (completed_lessons / total_lessons) >= 0.8:
        return True
    
    return False

def can_access_lesson(user, lesson):
    """
    Vérifie si un utilisateur peut accéder à une leçon
    """
    # Vérifier l'inscription au cours
    if not Enrollment.objects.filter(user=user, course=lesson.module.course).exists():
        return False, "Non inscrit au cours"
    
    # Vérifier si le module est accessible
    module_accessible, _ = can_access_course(user, lesson.module.course)
    if not module_accessible:
        return False, f"Module non accessible: {_}"
    
    # Vérifier l'ordre dans le module
    module_lessons = Lesson.objects.filter(module=lesson.module).order_by('order')
    lesson_index = list(module_lessons).index(lesson)
    
    # Première leçon toujours accessible
    if lesson_index == 0:
        return True, "Première leçon"
    
    # Vérifier la leçon précédente
    if lesson_index > 0:
        previous_lesson = module_lessons[lesson_index - 1]
        previous_progress = LessonProgress.objects.filter(
            user=user,
            lesson=previous_lesson
        ).first()
        
        if not previous_progress or not previous_progress.is_fully_completed:
            return False, f"Leçon précédente non terminée: {previous_lesson.title}"
    
    return True, "Leçon accessible"

def get_next_accessible_lesson(user, current_lesson):
    """
    Récupère la leçon suivante accessible
    """
    module_lessons = Lesson.objects.filter(module=current_lesson.module).order_by('order')
    current_index = list(module_lessons).index(current_lesson)
    
    # Chercher la prochaine leçon non complétée
    for i in range(current_index + 1, len(module_lessons)):
        lesson = module_lessons[i]
        progress = LessonProgress.objects.filter(user=user, lesson=lesson).first()
        
        if not progress or not progress.is_fully_completed:
            return lesson
    
    return None

def get_learning_path_progression(user):
    """
    Calcule la progression détaillée du parcours d'apprentissage
    """
    try:
        learning_path = user.learningpath_set.get()
    except LearningPath.DoesNotExist:
        return None
    
    # Récupérer tous les modules du parcours
    if learning_path.template:
        modules = learning_path.template.sequence.get('modules', [])
        
        progression_data = []
        for module_data in modules:
            module_id = module_data.get('id')
            
            # Trouver le module correspondant
            module_obj = None
            for module in Module.objects.all():
                if f"module_{module.order}" == module_id or module_id == module.get('id'):
                    module_obj = module
                    break
            
            if module_obj:
                # Calculer la progression du module
                is_completed = is_module_completed(user, module_obj)
                progress_percentage = calculate_module_progress(user, module_obj)
                
                progression_data.append({
                    'module_id': module_id,
                    'module_name': module_data.get('name'),
                    'order': module_data.get('order'),
                    'is_completed': is_completed,
                    'progress_percentage': progress_percentage,
                    'is_accessible': True,  # Sera vérifié avec can_access_course
                    'status': get_module_status(is_completed, progress_percentage)
                })
        
        return progression_data
    
    return []

def calculate_module_progress(user, module):
    """
    Calcule le pourcentage de progression d'un module
    """
    total_lessons = Lesson.objects.filter(module=module).count()
    if total_lessons == 0:
        return 0
    
    completed_lessons = LessonProgress.objects.filter(
        user=user,
        lesson__module=module,
        is_fully_completed=True
    ).count()
    
    return round((completed_lessons / total_lessons) * 100, 1)

def get_module_status(is_completed, progress_percentage):
    """
    Détermine le statut d'affichage d'un module
    """
    if is_completed:
        return "Terminé"
    elif progress_percentage >= 50:
        return "En cours"
    else:
        return "À commencer"

def update_learning_path_on_lesson_completion(user, lesson):
    """
    Met à jour le parcours quand une leçon est terminée
    """
    try:
        learning_path = user.learningpath_set.get()
        learning_path.last_activity = timezone.now()
        
        # Vérifier si toutes les leçons du module sont terminées
        module = lesson.module
        total_lessons = Lesson.objects.filter(module=module).count()
        completed_lessons = LessonProgress.objects.filter(
            user=user,
            lesson__module=module,
            is_fully_completed=True
        ).count()
        
        # Si toutes les leçons sont terminées, marquer le module comme complété
        if total_lessons > 0 and completed_lessons == total_lessons:
            # Ajouter le module aux cours complétés
            if not learning_path.completed_courses.filter(id=module.course).exists():
                learning_path.completed_courses.add(module.course)
            
            # Mettre à jour le cours actuel si nécessaire
            next_course = module.course.get_next_course()
            if next_course:
                learning_path.current_course = next_course
        
        learning_path.save()
        
    except LearningPath.DoesNotExist:
        pass
