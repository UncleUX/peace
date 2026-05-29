from .models import Course, Module, Lesson, LessonVideo

def duplicate_course(course, new_title=None):
    """
    Crée une copie du cours avec tous ses modules, leçons et vidéos associés
    """
    # Préparer le nouveau titre
    if not new_title:
        new_title = f"{course.title} (Copie)"
        
    # Créer une copie du cours avec les mêmes attributs
    course_copy = Course.objects.create(
        title=new_title,
        description=course.description,
        category=course.category,
        thumbnail=course.thumbnail,
        language=course.language,
        created_by=course.created_by,
        is_published=False  # Par défaut, la copie n'est pas publiée
    )
    
    # Copier les modules
    for module in course.modules.all():
        # Créer une copie du module
        module_copy = Module.objects.create(
            course=course_copy,
            title=module.title,
            description=module.description,
            level=module.level,
            order=module.order,
            is_locked=module.is_locked
        )
        
        # Copier les leçons
        for lesson in module.lessons.all():
            # Créer une copie de la leçon
            lesson_copy = Lesson.objects.create(
                module=module_copy,
                title=lesson.title,
                description=lesson.description,
                content_file=lesson.content_file,
                order=lesson.order,
                is_active=lesson.is_active,
                thumbnail=lesson.thumbnail,
                duration=lesson.duration,
                subtitle_file=lesson.subtitle_file
            )
            
            # Copier les vidéos de la leçon
            for video in lesson.videos.all():
                LessonVideo.objects.create(
                    lesson=lesson_copy,
                    title=video.title,
                    video_file=video.video_file,
                    order=video.order,
                    duration=video.duration
                )
    
    return course_copy
