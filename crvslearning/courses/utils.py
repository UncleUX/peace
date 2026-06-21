import os
import subprocess
import tempfile
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


def apply_faststart_to_video(video_file_path):
    """
    Applique l'option faststart de ffmpeg à une vidéo MP4.
    Cela déplace les métadonnées (moov atom) au début du fichier,
    permettant un démarrage plus rapide de la lecture.

    Args:
        video_file_path: Chemin vers le fichier vidéo

    Returns:
        Chemin vers le fichier optimisé, ou le chemin original si échec
    """
    try:
        # Vérifier que ffmpeg est installé
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("ffmpeg n'est pas installé ou n'est pas dans le PATH")
        return video_file_path

    # Créer un fichier temporaire pour la vidéo optimisée
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, f'faststart_{os.path.basename(video_file_path)}')

    try:
        # Commande ffmpeg avec faststart
        # -c copy: copie les flux sans ré-encodage (rapide)
        # -movflags +faststart: déplace les métadonnées au début
        cmd = [
            'ffmpeg',
            '-i', video_file_path,
            '-c', 'copy',
            '-movflags', '+faststart',
            '-y',  # Écraser le fichier de sortie s'il existe
            temp_path
        ]

        # Exécuter la commande
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            # Remplacer le fichier original par le fichier optimisé
            import shutil
            shutil.move(temp_path, video_file_path)
            print(f"Faststart appliqué avec succès à {video_file_path}")
            return video_file_path
        else:
            print(f"Erreur ffmpeg: {result.stderr}")
            # Nettoyer le fichier temporaire en cas d'erreur
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return video_file_path

    except Exception as e:
        print(f"Erreur lors de l'application du faststart: {e}")
        # Nettoyer le fichier temporaire en cas d'erreur
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return video_file_path
