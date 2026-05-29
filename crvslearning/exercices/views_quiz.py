from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
import random
import hashlib
from datetime import datetime

from courses.models import Lesson, LearningPath, LessonProgress
from .models import Exercise, UserExerciseAttempt
from payments.models import ModuleAccess, Payment

class QuizView(LoginRequiredMixin, View):
    def _check_module_completion(self, request, module, user=None):
        """
        Vérifie si l'utilisateur a complété toutes les leçons du module
        et réussi le quiz avant de déverrouiller le module suivant
        """
        from .models import Exercise, UserExerciseAttempt
        
        # Si user n'est pas fourni, l'extraire de request
        if user is None:
            user = request.user
        
        # Vérifier si l'utilisateur a réussi le quiz du module
        quiz_passed = False
        for lesson in module.lessons.all():
            # Vérifier si la leçon a des exercices (quiz)
            if Exercise.objects.filter(lesson=lesson).exists():
                # Vérifier si l'utilisateur a répondu correctement à tous les exercices
                exercises = Exercise.objects.filter(lesson=lesson)
                user_attempts = UserExerciseAttempt.objects.filter(
                    user=user,
                    exercise__in=exercises
                )
                
                # Calculer le score
                correct_answers = user_attempts.filter(is_correct=True).count()
                total_questions = exercises.count()
                score = (correct_answers / total_questions * 100) if total_questions > 0 else 0
                quiz_passed = score >= 80  # Seuil de réussite à 80%
                
                if not quiz_passed:
                    return  # Ne pas déverrouiller si le quiz n'est pas réussi
        
        # Si le quiz est réussi, marquer SEULEMENT la leçon concernée comme complétée
        if quiz_passed:
            # Trouver la leçon spécifique qui a le quiz réussi
            lesson_with_quiz = None
            for lesson in module.lessons.all():
                if Exercise.objects.filter(lesson=lesson).exists():
                    exercises = Exercise.objects.filter(lesson=lesson)
                    user_attempts = UserExerciseAttempt.objects.filter(
                        user=user,
                        exercise__in=exercises
                    )
                    
                    # Calculer le score pour cette leçon spécifique
                    correct_answers = user_attempts.filter(is_correct=True).count()
                    total_questions = exercises.count()
                    score = (correct_answers / total_questions * 100) if total_questions > 0 else 0
                    
                    if score >= 80:  # Seuil de réussite
                        lesson_with_quiz = lesson
                        break
            
            # Marquer SEULEMENT la leçon avec le quiz réussi comme complétée
            if lesson_with_quiz:
                LessonProgress.objects.update_or_create(
                    user=user,
                    lesson=lesson_with_quiz,
                    defaults={
                        'is_completed': True,
                        'completed_at': timezone.now()
                    }
                )
                
                # Vérifier si TOUTES les leçons du module sont maintenant complétées
                all_lessons_completed = True
                for lesson in module.lessons.all():
                    if not LessonProgress.objects.filter(user=user, lesson=lesson, is_completed=True).exists():
                        all_lessons_completed = False
                        break
                
                # Seulement si TOUTES les leçons sont complétées, déverrouiller le module suivant
                if all_lessons_completed:
                    # Trouver le module suivant dans le cours
                    next_module = module.course.modules.filter(
                        order__gt=module.order
                    ).order_by('order').first()
                    
                    if next_module:
                        # Créer un accès individuel pour l'utilisateur au module suivant
                        
                        # Créer un paiement gratuit pour cet accès
                        payment = Payment.objects.create(
                            user=user,
                            module=next_module,
                            amount=0,
                            status='completed',
                            payment_method='quiz_completion',
                            transaction_id=f'quiz_{user.id}_{module.id}_{timezone.now().timestamp()}'
                        )
                        
                        # Créer l'accès au module
                        ModuleAccess.objects.update_or_create(
                            user=user,
                            module=next_module,
                            defaults={
                                'payment': payment,
                                'granted_at': timezone.now(),
                                'expires_at': None,  # Accès permanent
                                'is_active': True
                            }
                        )
                
                        # Mettre à jour le parcours d'apprentissage avec le prochain module
                        learning_path, created = LearningPath.objects.get_or_create(
                            user=user,
                            defaults={'current_lesson': next_module.lessons.first()}
                        )
                        if not created:
                            learning_path.current_lesson = next_module.lessons.first()
                        
                        # Ajouter un message pour informer l'utilisateur
                        messages.success(
                            request,
                            f"Félicitations ! Vous avez réussi le module et débloqué le suivant : {next_module.title}"
                        )
    
    def get_user_answers(self, request, exercises):
        """Récupère les réponses de l'utilisateur pour les exercices donnés"""
        user_answers = {}
        if request.session.get('quiz_answers'):
            quiz_answers = request.session['quiz_answers']
            for exercise in exercises:
                if str(exercise.id) in quiz_answers:
                    user_answers[exercise.id] = quiz_answers[str(exercise.id)]
        return user_answers
    
    def save_user_answer(self, request, exercise_id, choice_id):
        """Sauvegarde la réponse de l'utilisateur en session"""
        if 'quiz_answers' not in request.session:
            request.session['quiz_answers'] = {}
        
        request.session['quiz_answers'][str(exercise_id)] = choice_id
        request.session.modified = True
    
    def generate_quiz_seed(self, user_id, lesson_id, attempt_number=1):
        """Génère un seed unique pour la randomisation du jour et du nombre de tentatives"""
        date_key = datetime.now().strftime('%Y-%m-%d')
        seed_string = f"{user_id}-{lesson_id}-{date_key}-attempt-{attempt_number}"
        return int(hashlib.md5(seed_string.encode()).hexdigest()[:8], 16)
    
    def get_randomized_exercises(self, user, lesson, max_questions=5, force_new_randomization=False):
        """Récupère et randomise les questions pour le quiz"""
        # Compter le nombre de tentatives précédentes pour cette leçon
        from .models import UserExerciseAttempt
        previous_attempts = UserExerciseAttempt.objects.filter(
            user=user,
            exercise__lesson=lesson
        ).values('exercise').distinct().count()
        
        # Déterminer le numéro de tentative actuel
        attempt_number = max(1, previous_attempts + 1)
        
        # Si forcé, incrémenter le numéro de tentative pour changer la randomisation
        if force_new_randomization:
            attempt_number += 1
        
        # 1. Récupérer toutes les questions disponibles
        all_exercises = list(lesson.exercises.all().prefetch_related('choices'))
        
        # 2. Limiter à max_questions si nécessaire
        if len(all_exercises) > max_questions:
            # Utiliser le seed pour la sélection aléatoire
            seed = self.generate_quiz_seed(user.id, lesson.id, attempt_number)
            random.seed(seed)
            selected_exercises = random.sample(all_exercises, max_questions)
        else:
            selected_exercises = all_exercises
        
        # 3. Randomiser l'ordre avec un seed différent
        order_seed = self.generate_quiz_seed(user.id, lesson.id, attempt_number) + 1  # +1 pour différencier
        random.seed(order_seed)
        random.shuffle(selected_exercises)
        
        return selected_exercises
    
    template_name = 'exercices/quiz_step.html'
    
    def get(self, request, lesson_id):
        lesson = get_object_or_404(Lesson, id=lesson_id)
        
        # Vérifier si l'utilisateur demande une nouvelle tentative
        force_new_randomization = request.GET.get('retry', 'false').lower() == 'true'
        
        # NOUVELLE LOGIQUE : Randomisation des questions
        exercises_list = self.get_randomized_exercises(request.user, lesson, max_questions=5, force_new_randomization=force_new_randomization)
        
        # Vérifier si l'utilisateur est inscrit au cours
        if not request.user.enrollments.filter(course=lesson.module.course).exists():
            messages.warning(request, "Vous devez être inscrit au cours pour accéder aux exercices.")
            return redirect('courses:course_detail', course_id=lesson.module.course.id)
        
        # Initialiser la question courante
        current_question = int(request.GET.get('q', 0))
        
        # Valider l'index de la question
        if current_question < 0 or current_question >= len(exercises_list):
            current_question = 0
        
        # Récupérer l'exercice actuel
        current_exercise = exercises_list[current_question] if exercises_list else None
        
        # Calculer le pourcentage de progression
        total_exercises = len(exercises_list)
        progress_percentage = int(((current_question + 1) / total_exercises * 100)) if total_exercises > 0 else 0
        
        # Calculer s'il y a une question suivante
        has_next_question = current_question < (len(exercises_list) - 1)
        
        # Stocker l'ordre des questions en session pour la cohérence
        request.session[f'quiz_order_{lesson_id}'] = [ex.id for ex in exercises_list]
        request.session.modified = True
        
        # Gérer le timer du quiz - FORCER le démarrage si c'est la première question
        import time
        current_time = time.time()
        quiz_start_time = request.session.get('quiz_start_time')
        
        # Toujours démarrer un nouveau timer si c'est la première question ou si aucun timer n'existe
        if current_question == 0 or not quiz_start_time:
            quiz_start_time = current_time
            request.session['quiz_start_time'] = quiz_start_time
            request.session['quiz_lesson_id'] = lesson_id  # Associer le timer à cette leçon
            request.session.modified = True
        else:
            # Vérifier que le timer est bien pour cette leçon
            session_lesson_id = request.session.get('quiz_lesson_id')
            if session_lesson_id != lesson_id:
                # Nouvelle leçon, redémarrer le timer
                quiz_start_time = current_time
                request.session['quiz_start_time'] = quiz_start_time
                request.session['quiz_lesson_id'] = lesson_id
                request.session.modified = True
        
        # Récupérer les réponses de l'utilisateur
        user_answers = self.get_user_answers(request, exercises_list)
        
        context = {
            'lesson': lesson,
            'exercises': exercises_list,
            'current_exercise': current_exercise,
            'current_question': current_question,
            'progress_percentage': progress_percentage,
            'has_next_question': has_next_question,
            'quiz_start_time': quiz_start_time,
            'current_time': current_time,  # Ajouter le temps actuel pour le calcul
            'user_answers': user_answers,
            'course': lesson.module.course,
        }
        return render(request, self.template_name, context)
    
    def post(self, request, lesson_id):
        lesson = get_object_or_404(Lesson, id=lesson_id)
        
        # Récupérer les mêmes exercices randomisés que dans get()
        exercises = self.get_randomized_exercises(request.user, lesson, max_questions=5)
        
        # Récupérer l'action demandée
        action = request.POST.get('action', 'next')
        current_question = int(request.POST.get('current_question', 0))
        
        # Sauvegarder la réponse actuelle si présente
        for key, value in request.POST.items():
            if key.startswith('exercise_'):
                exercise_id = int(key.replace('exercise_', ''))
                self.save_user_answer(request, exercise_id, value)
        
        # Gérer la navigation
        if action == 'previous' and current_question > 0:
            return redirect(f'{request.path}?q={current_question - 1}')
        elif action == 'next' and current_question < len(exercises) - 1:
            return redirect(f'{request.path}?q={current_question + 1}')
        elif action == 'goto_question':
            goto_question = int(request.POST.get('goto_question', 0))
            if 0 <= goto_question < len(exercises):
                return redirect(f'{request.path}?q={goto_question}')
        elif action == 'submit':
            # Traiter toutes les réponses et soumettre le quiz
            return self.submit_quiz(request, lesson, exercises)
        
        # Redirection par défaut
        return redirect(request.path)
    
    def submit_quiz(self, request, lesson, exercises):
        """Traite la soumission finale du quiz"""
        # Récupérer les réponses de la session
        quiz_answers = request.session.get('quiz_answers', {})
        
        # Calculer le temps total passé
        import time
        quiz_start_time = request.session.get('quiz_start_time')
        total_time_seconds = 0
        if quiz_start_time:
            total_time_seconds = int(time.time() - quiz_start_time)
        
        # Traiter les réponses
        results = []
        correct_answers = 0
        exercises_dict = {ex.id: ex for ex in exercises}
        answered_questions = 0
        
        for exercise_id_str, choice_id in quiz_answers.items():
            exercise_id = int(exercise_id_str)
            exercise = exercises_dict.get(exercise_id)
            
            if not exercise:
                continue
                
            answered_questions += 1
            selected_choice = exercise.choices.filter(id=choice_id).first()
            
            if selected_choice:
                # Enregistrer la tentative
                attempt, created = UserExerciseAttempt.objects.update_or_create(
                    user=request.user,
                    exercise=exercise,
                    defaults={
                        'selected_choice': selected_choice,
                        'is_correct': selected_choice.is_correct
                    }
                )
                
                results.append({
                    'exercise': exercise,
                    'selected_choice': selected_choice,
                    'is_correct': selected_choice.is_correct,
                    'explanation': selected_choice.explanation or ""
                })
                
                if selected_choice.is_correct:
                    correct_answers += 1
        
        # Nettoyer la session
        if 'quiz_answers' in request.session:
            del request.session['quiz_answers']
        if 'quiz_start_time' in request.session:
            del request.session['quiz_start_time']
        if 'quiz_lesson_id' in request.session:
            del request.session['quiz_lesson_id']
        request.session.modified = True
        
        # Calculer le score uniquement sur les questions répondues (5 maximum)
        total_questions_for_score = min(answered_questions, len(exercises))
        score = int((correct_answers / total_questions_for_score) * 100) if total_questions_for_score > 0 else 0
        quiz_passed = score >= 100  # Seuil de réussite à 100% (5/5)
        
        # Mettre à jour la progression de l'utilisateur si le quiz est réussi
        if quiz_passed:
            # Récupérer ou créer le parcours d'apprentissage
            learning_path, created = LearningPath.objects.get_or_create(user=request.user)
            
            # Marquer la leçon comme complétée
            lesson_progress, _ = LessonProgress.objects.update_or_create(
                user=request.user,
                lesson=lesson,
                defaults={
                    'is_completed': True,
                    'completed_at': timezone.now()
                }
            )
            
            # Mettre à jour le parcours d'apprentissage
            learning_path.current_lesson = lesson
            learning_path.current_course = lesson.module.course
            learning_path.save()
            
            # Vérifier si le module est complété
            self._check_module_completion(request, lesson.module)
        
        context = {
            'lesson': lesson,
            'results': results,
            'score': score,
            'total_questions': total_questions_for_score,
            'correct_answers': correct_answers,
            'quiz_passed': quiz_passed,
            'total_time_seconds': total_time_seconds,
            'course': lesson.module.course,
            'can_retry': score < 100,  # Permettre de réessayer si score < 100%
        }
        return render(request, 'exercices/quiz_results.html', context)
