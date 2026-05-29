from django.core.management.base import BaseCommand
import whisper
import os
from django.core.files import File
from courses.models import Lesson

class Command(BaseCommand):
    help = 'Generate subtitles for a lesson video using Whisper'

    def add_arguments(self, parser):
        parser.add_argument('lesson_id', type=int, help='ID de la leçon')

    def handle(self, *args, **options):
        lesson_id = options['lesson_id']
        try:
            lesson = Lesson.objects.get(id=lesson_id)
            
            if not lesson.video_file:
                self.stdout.write(self.style.ERROR('Aucune vidéo trouvée pour cette leçon'))
                return

            self.stdout.write(f'Début de la génération des sous-titres pour la leçon: {lesson.title}')
            
            # Charger le modèle Whisper (tiny pour la vitesse, base pour un bon équilibre)
            model = whisper.load_model("base")
            
            # Transcrire la vidéo
            self.stdout.write('Transcription en cours... (cela peut prendre plusieurs minutes)')
            result = model.transcribe(lesson.video_file.path, language='fr')
            
            # Créer le contenu VTT
            vtt_content = "WEBVTT\n\n"
            for i, segment in enumerate(result['segments'], 1):
                start = segment['start']
                end = segment['end']
                text = segment['text'].strip()
                vtt_content += f"{i}\n"
                vtt_content += f"{int(start//3600):02d}:{int((start%3600)//60):02d}:{start%60:06.3f} --> "
                vtt_content += f"{int(end//3600):02d}:{int((end%3600)//60):02d}:{end%60:06.3f}\n"
                vtt_content += f"{text}\n\n"
            
            # Créer le dossier s'il n'existe pas
            os.makedirs('media/subtitles', exist_ok=True)
            vtt_path = f"media/subtitles/lesson_{lesson.id}.vtt"
            
            # Sauvegarder le fichier
            with open(vtt_path, 'w', encoding='utf-8') as f:
                f.write(vtt_content)
            
            # Associer au modèle
            with open(vtt_path, 'rb') as f:
                lesson.subtitle_file.save(f'lesson_{lesson.id}.vtt', File(f), save=True)
            
            self.stdout.write(self.style.SUCCESS(f'Sous-titres générés avec succès: {lesson.subtitle_file.url}'))
            
        except Lesson.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Leçon avec l\'ID {lesson_id} non trouvée'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erreur lors de la génération: {str(e)}'))
