from django.views.generic import CreateView, UpdateView, DetailView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.forms import inlineformset_factory
from .models import Exercise, Choice, UserExerciseAttempt
from .forms import ChoiceForm
from courses.models import Lesson

class ExerciseCreateView(LoginRequiredMixin, CreateView):
    model = Exercise
    fields = ['question', 'order']
    template_name = 'exercices/exercise_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lesson = get_object_or_404(Lesson, id=self.kwargs['lesson_id'])
        context['lesson'] = lesson
        
        # Récupérer tous les exercices de la leçon
        context['exercises'] = Exercise.objects.filter(lesson=lesson).order_by('order')
        
        if self.request.POST:
            context['formset'] = self.get_formset(self.request.POST)
        else:
            context['formset'] = self.get_formset()
            
        return context
        
    def get_formset(self, data=None):
        ChoiceFormSet = inlineformset_factory(
            Exercise,
            Choice,
            form=ChoiceForm,
            extra=3,
            can_delete=True
        )
        return ChoiceFormSet(instance=self.object, data=data, prefix='choices')
        
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        
        if formset.is_valid():
            self.object = form.save(commit=False)
            self.object.lesson = get_object_or_404(Lesson, id=self.kwargs['lesson_id'])
            self.object.save()
            formset.instance = self.object
            formset.save()
            messages.success(self.request, 'Exercice enregistré avec succès!')
            return super().form_valid(form)
        else:
            return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse_lazy('exercices:exercise_edit', kwargs={'pk': self.object.pk})

class ExerciseUpdateView(LoginRequiredMixin, UpdateView):
    model = Exercise
    fields = ['question', 'order']
    template_name = 'exercices/exercise_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lesson = self.object.lesson
        context['lesson'] = lesson
        context['exercises'] = Exercise.objects.filter(lesson=lesson).exclude(pk=self.object.pk).order_by('order')
        
        if self.request.POST:
            context['formset'] = self.get_formset(self.request.POST, instance=self.object)
        else:
            context['formset'] = self.get_formset(instance=self.object)
            
        return context
        
    def get_formset(self, data=None, instance=None):
        ChoiceFormSet = inlineformset_factory(
            Exercise,
            Choice,
            form=ChoiceForm,
            extra=1,
            can_delete=True
        )
        return ChoiceFormSet(instance=instance, data=data, prefix='choices')
        
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        
        if formset.is_valid():
            response = super().form_valid(form)
            formset.instance = self.object
            formset.save()
            messages.success(self.request, 'Exercice mis à jour avec succès!')
            return response
        else:
            return self.render_to_response(self.get_context_data(form=form))
    
    def get_success_url(self):
        return reverse_lazy('exercices:exercise_edit', kwargs={'pk': self.object.pk})

@login_required
@require_POST
def submit_attempt(request, exercise_id):
    exercise = get_object_or_404(Exercise, id=exercise_id)
    choice_id = request.POST.get('choice_id')
    
    if not choice_id:
        return JsonResponse({'error': 'Veuillez sélectionner une réponse'}, status=400)
    
    try:
        selected_choice = exercise.choices.get(id=choice_id)
    except Choice.DoesNotExist:
        return JsonResponse({'error': 'Choix invalide'}, status=400)
    
    # Créer ou mettre à jour la tentative
    attempt, created = UserExerciseAttempt.objects.update_or_create(
        user=request.user,
        exercise=exercise,
        defaults={
            'selected_choice': selected_choice,
            'is_correct': selected_choice.is_correct
        }
    )
    
    # Vérifier si toutes les leçons du module sont complétées
    lesson = exercise.lesson
    module = lesson.module
    course = module.course
    
    # Marquer la leçon comme complétée si tous les exercices sont réussis
    from courses.models import LessonProgress
    all_exercises = lesson.exercises.all()
    user_attempts = UserExerciseAttempt.objects.filter(
        user=request.user, 
        exercise__in=all_exercises,
        is_correct=True
    )
    
    if user_attempts.count() == all_exercises.count():
        # Marquer la leçon comme complétée
        lesson_progress, created = LessonProgress.objects.get_or_create(
            user=request.user,
            lesson=lesson,
            defaults={'is_completed': True}
        )
        if not created and not lesson_progress.is_completed:
            lesson_progress.is_completed = True
            lesson_progress.save()
        
        # Vérifier si toutes les leçons du module sont complétées
        all_lessons = module.lessons.all()
        completed_lessons = LessonProgress.objects.filter(
            user=request.user,
            lesson__in=all_lessons,
            is_completed=True
        )
        
        if completed_lessons.count() == all_lessons.count():
            # Déverrouiller le module suivant
            next_module = course.modules.filter(order=module.order + 1).first()
            if next_module:
                next_module.is_locked = False
                next_module.save()
                
                return JsonResponse({
                    'correct': selected_choice.is_correct,
                    'explanation': selected_choice.explanation or '',
                    'module_unlocked': True,
                    'next_module': next_module.title,
                    'message': f'Félicitations ! Module "{next_module.title}" déverrouillé !'
                })
    
    return JsonResponse({
        'correct': selected_choice.is_correct,
        'explanation': selected_choice.explanation or '',
        'module_unlocked': False
    })