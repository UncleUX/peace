from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView
from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.core.paginator import Paginator
from .models import Question, Answer, Vote, Category, QuestionView, QuestionVote, Comment
from .forms import QuestionForm, AnswerForm, ValidationForm

class ForumHomeView(ListView):
    """Page d'accueil du forum"""
    model = Question
    template_name = 'forum/forum_home.html'
    context_object_name = 'questions'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = Question.objects.all()
        
        # Filtrage par catégorie
        category_id = self.request.GET.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Recherche
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(content__icontains=search_query) |
                Q(tags__icontains=search_query)
            )
        
        # Filtrer par cours/module/leçon
        course_id = self.request.GET.get('course')
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['search_query'] = self.request.GET.get('search', '')
        context['selected_category'] = self.request.GET.get('category', '')
        context['sort'] = self.request.GET.get('sort', 'recent')
        
        # Top Contributors globaux pour le forum
        from django.db.models import Count
        from django.db.models import Q
        
        # Calculer les top contributors globaux (toutes les questions)
        global_top_contributors = []
        contributor_data = {}
        
        # Compter les contributions par utilisateur sur tout le forum
        from .models import Answer as AnswerModel
        all_answers = AnswerModel.objects.select_related('author')
        for answer in all_answers:
            author = answer.author
            if author not in contributor_data:
                contributor_data[author] = {
                    'answers_count': 0,
                    'total_votes': 0,
                    'validated_answers': 0,
                    'user': author
                }
            
            contributor_data[author]['answers_count'] += 1
            contributor_data[author]['total_votes'] += answer.total_votes
            if answer.is_validated:
                contributor_data[author]['validated_answers'] += 1
        
        # Trier par score (réponses validées + votes)
        sorted_global_contributors = sorted(
            contributor_data.values(),
            key=lambda x: (x['validated_answers'] * 10 + x['total_votes']),
            reverse=True
        )[:10]  # Top 10 globaux
        
        context['global_top_contributors'] = sorted_global_contributors
        
        # Statistiques réelles
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models import Count
        
        now = timezone.now()
        week_ago = now - timedelta(days=7)
        
        # Questions cette semaine
        week_questions = Question.objects.filter(created_at__gte=week_ago)
        context['questions_this_week'] = week_questions.count()
        
        # Réponses cette semaine
        week_answers = AnswerModel.objects.filter(created_at__gte=week_ago)
        context['answers_this_week'] = week_answers.count()
        
        # Total des questions
        context['total_questions'] = Question.objects.count()
        
        # Tags populaires pour la sidebar
        popular_tags = []
        all_questions = Question.objects.all()
        for question in all_questions:
            if question.tags:
                tags = [tag.strip() for tag in question.tags.split(',')]
                for tag in tags:
                    if tag:
                        # Compter les questions avec ce tag
                        tag_count = Question.objects.filter(tags__icontains=tag).count()
                        popular_tags.append({'name': tag, 'count': tag_count})
        
        # Dédoublonner et trier les tags
        unique_tags = []
        seen = set()
        for tag in popular_tags:
            if tag['name'] not in seen:
                seen.add(tag['name'])
                unique_tags.append(tag)
        
        context['popular_tags'] = sorted(unique_tags, key=lambda x: x['count'], reverse=True)[:10]
        
        # Cours avec nombre de questions pour la sidebar
        from courses.models import Course
        courses = Course.objects.annotate(question_count=Count('course_questions')).filter(question_count__gt=0)
        context['courses'] = courses[:5]  # Limiter à 5 cours
        
        # Questions populaires (plus vues) pour la sidebar
        context['popular_questions'] = Question.objects.order_by('-views_count')[:5]
        
        # Questions récentes pour la sidebar
        context['recent_questions'] = Question.objects.order_by('-created_at')[:5]
        
        # === SYSTÈME AUTOMATIQUE COMPLET DE POINTS ===
        
        # Tous les utilisateurs de la plateforme
        from users.models import CustomUser
        all_users = CustomUser.objects.filter(is_active=True).order_by('-date_joined')
        
        # Variables pour les calculs
        today = timezone.now().date()
        week_ago = timezone.now() - timedelta(days=7)
        
        # Fonction de calcul automatique
        def calculate_complete_auto_score(user):
            from datetime import timedelta
            from .models import Comment
            
            # Points de base automatiques
            questions_points = Question.objects.filter(author=user).count() * 8
            answers_points = AnswerModel.objects.filter(author=user).count() * 3
            comments_points = Comment.objects.filter(author=user).count() * 2
            
            # Points de qualité automatiques
            user_answers = AnswerModel.objects.filter(author=user)
            user_comments = Comment.objects.filter(author=user)
            
            quality_bonus = 0
            
            # Bonus pour réponses détaillées
            for answer in user_answers:
                if len(answer.content) > 200:
                    quality_bonus += 3
                elif len(answer.content) > 100:
                    quality_bonus += 1
                    
                # Bonus pour rapidité de réponse
                if answer.created_at <= answer.question.created_at + timedelta(hours=24):
                    quality_bonus += 2
            
            # Bonus pour commentaires détaillés
            for comment in user_comments:
                if len(comment.content) > 50:
                    quality_bonus += 1
                    
                # Bonus pour rapidité de commentaire
                if comment.created_at <= comment.answer.created_at + timedelta(hours=2):
                    quality_bonus += 1
            
            # Bonus de régularité
            total_activities = questions_points + answers_points + comments_points
            if total_activities >= 50:
                regularity_bonus = 25
            elif total_activities >= 20:
                regularity_bonus = 15
            elif total_activities >= 10:
                regularity_bonus = 10
            else:
                regularity_bonus = 0
            
            # Votes reçus (automatique)
            votes_points = sum(answer.total_votes or 0 for answer in user_answers)
            
            total_score = (
                questions_points + 
                answers_points + 
                comments_points + 
                quality_bonus + 
                regularity_bonus + 
                votes_points
            )
            
            return total_score
        
        # Préparer les données des membres avec leurs statistiques
        members_data = []
        for user in all_users:
            # Compter les questions, réponses et commentaires de l'utilisateur
            user_questions = Question.objects.filter(author=user)
            user_answers = AnswerModel.objects.filter(author=user)
            user_comments = Comment.objects.filter(author=user)
            
            # Utiliser le calcul automatique complet
            user_score = calculate_complete_auto_score(user)
            
            # Déterminer le statut de l'utilisateur
            is_active_today = (
                user.last_login and user.last_login.date() == today or
                user_questions.filter(created_at__date=today).exists() or
                user_answers.filter(created_at__date=today).exists() or
                user_comments.filter(created_at__date=today).exists()
            )
            
            members_data.append({
                'user': user,
                'questions_count': user_questions.count(),
                'answers_count': user_answers.count(),
                'comments_count': user_comments.count(),
                'score': user_score,
                'is_active_today': is_active_today,
                'last_login': user.last_login,
                'date_joined': user.date_joined
            })
        
        # Trier par score (top contributeurs en premier)
        members_data.sort(key=lambda x: x['score'], reverse=True)
        
        # Séparer les top contributeurs et les autres membres
        context['top_contributors'] = members_data[:5]  # Top 5
        context['all_members'] = members_data  # Tous les membres
        
        # Statistiques globales
        context['total_members'] = all_users.count()
        context['active_today'] = len([m for m in members_data if m['is_active_today']])
        context['new_this_week'] = all_users.filter(date_joined__gte=week_ago).count()
        
        # Activité récente des membres
        recent_activities = []
        
        # Questions récentes
        recent_questions = Question.objects.select_related('author').order_by('-created_at')[:5]
        for question in recent_questions:
            recent_activities.append({
                'type': 'question',
                'user': question.author,
                'content': f'a posé une question: {question.title[:50]}...',
                'timestamp': question.created_at,
                'icon': 'bi-question-circle'
            })
        
        # Réponses récentes
        recent_answers = AnswerModel.objects.select_related('author').order_by('-created_at')[:5]
        for answer in recent_answers:
            recent_activities.append({
                'type': 'answer',
                'user': answer.author,
                'content': f'a répondu à une question',
                'timestamp': answer.created_at,
                'icon': 'bi-chat-dots'
            })
        
        # Nouveaux membres récents
        new_members = all_users.filter(date_joined__gte=week_ago).order_by('-date_joined')[:3]
        for user in new_members:
            recent_activities.append({
                'type': 'new_member',
                'user': user,
                'content': f'a rejoint la communauté',
                'timestamp': user.date_joined,
                'icon': 'bi-person-plus'
            })
        
        # Trier par timestamp et limiter
        recent_activities.sort(key=lambda x: x['timestamp'], reverse=True)
        context['recent_activities'] = recent_activities[:10]
        
        return context

class QuestionDetailView(DetailView):
    """Détail d'une question"""
    model = Question
    template_name = 'forum/question_detail.html'
    
    def get_object(self):
        """Récupère la question et incrémente les vues"""
        queryset = Question.objects.select_related('author', 'category', 'course', 'module', 'lesson')
        question = super().get_object()
        
        # Incrémenter le compteur de vues avec protection
        self._increment_view_count(question)
        
        return question
    
    def _increment_view_count(self, question):
        """Incrémente les vues avec protection contre les abus"""
        # Clé de session pour éviter les doublons
        session_key = f'viewed_question_{question.pk}'
        last_view_timestamp = self.request.session.get(session_key)
        
        # Vérifier si c'est un nouveau visiteur ou si le délai est passé (1 heure)
        from django.utils import timezone
        from datetime import timedelta
        
        # Convertir le timestamp en datetime si il existe
        last_view = None
        if last_view_timestamp:
            try:
                from datetime import datetime
                last_view = datetime.fromtimestamp(float(last_view_timestamp))
                last_view = timezone.make_aware(last_view)
            except:
                # Si la conversion échoue, considérer comme nouvelle visite
                last_view = None
        
        if not last_view or last_view < timezone.now() - timedelta(hours=1):
            question.views_count += 1
            question.save(update_fields=['views_count'])
            # Stocker le timestamp (compatible JSON)
            self.request.session[session_key] = str(timezone.now().timestamp())
            
            # Enregistrer la vue pour les statistiques détaillées
            if self.request.user.is_authenticated:
                from forum.models import QuestionView
                QuestionView.objects.get_or_create(
                    question=question,
                    user=self.request.user
                )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        question = self.object  # Utiliser self.object déjà récupéré
        
        # Récupérer les réponses (les votes sont calculés par les propriétés du modèle)
        answers = question.question_answers.select_related('author', 'validated_by').prefetch_related('answer_votes')
        
        context['answers'] = answers
        context['can_validate'] = (
            self.request.user.is_authenticated and 
            (question.author == self.request.user or self.request.user.is_staff or self.request.user.is_superuser)
        )
        
        # Top Contributors pour cette question
        top_contributors = []
        contributors_data = {}
        
        # Utiliser les réponses déjà récupérées (évite le conflit avec Answer)
        for answer in answers:
            author = answer.author
            if author not in contributors_data:
                contributors_data[author] = {
                    'answers_count': 0,
                    'total_votes': 0,
                    'validated_answers': 0,
                    'user': author
                }
            
            contributors_data[author]['answers_count'] += 1
            contributors_data[author]['total_votes'] += answer.total_votes
            if answer.is_validated:
                contributors_data[author]['validated_answers'] += 1
        
        # Trier par score (réponses validées + votes)
        sorted_contributors = sorted(
            contributors_data.values(),
            key=lambda x: (x['validated_answers'] * 10 + x['total_votes']),
            reverse=True
        )[:5]  # Top 5
        
        context['top_contributors'] = sorted_contributors
        
        # Formulaire de réponse
        context['form'] = AnswerForm()  # ← Plus d'argument 'user'
        
        return context
    
    def can_user_validate(self, user):
        """Vérifier si l'utilisateur peut valider (formateur, admin)"""
        return user.is_staff or user.is_superuser or hasattr(user, 'is_formateur')

class CreateQuestionView(LoginRequiredMixin, CreateView):
    """Créer une nouvelle question"""
    model = Question
    form_class = QuestionForm
    template_name = 'forum/create_question.html'
    
    def get_form_kwargs(self):
        """Passer l'utilisateur au formulaire"""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.author = self.request.user
        messages.success(self.request, 'Votre question a été publiée avec succès !')
        return super().form_valid(form)

@login_required
def answer_question(request, pk):
    """Répondre à une question"""
    question = get_object_or_404(Question, pk=pk)
    
    if question.is_closed:
        messages.error(request, 'Cette question est fermée aux nouvelles réponses.')
        return redirect('forum:question_detail', pk=pk)
    
    if request.method == 'POST':
        form = AnswerForm(request.POST)
        if form.is_valid():
            answer = form.save(commit=False)
            answer.author = request.user
            answer.question = question
            answer.save()
            
            messages.success(request, 'Votre réponse a été publiée avec succès !')
            return redirect('forum:question_detail', pk=pk)
    else:
        form = AnswerForm()
    
    return render(request, 'forum/answer_question.html', {
        'question': question,
        'form': form
    })

@login_required
def vote_question(request, pk):
    """Voter pour une question"""
    question = get_object_or_404(Question, pk=pk)
    
    if request.method == 'POST':
        vote_type = request.POST.get('vote_type', 'up')  # up ou down
        
        # Debug
        print(f"DEBUG: vote_type = {vote_type}")
        print(f"DEBUG: user = {request.user}")
        print(f"DEBUG: question = {question}")
        
        # Vérifier si l'utilisateur a déjà voté
        existing_vote = QuestionVote.objects.filter(user=request.user, question=question).first()
        print(f"DEBUG: existing_vote = {existing_vote}")
        
        if existing_vote:
            # Si le vote est le même, l'annuler
            if existing_vote.vote_type == vote_type:
                existing_vote.delete()
                messages.info(request, 'Votre vote a été annulé.')
            else:
                # Sinon, changer le type de vote
                existing_vote.vote_type = vote_type
                existing_vote.save()
                messages.success(request, 'Votre vote a été mis à jour !')
        else:
            try:
                # Créer le nouveau vote
                vote = QuestionVote.objects.create(user=request.user, question=question, vote_type=vote_type)
                print(f"DEBUG: vote créé = {vote}")
                messages.success(request, 'Votre vote a été enregistré !')
            except Exception as e:
                print(f"DEBUG: Erreur création vote = {e}")
                messages.error(request, f'Erreur lors du vote: {e}')
        
        # Vérifier le nombre de votes après création
        total_votes = QuestionVote.objects.filter(question=question).count()
        print(f"DEBUG: Total votes après = {total_votes}")
        
        return redirect('forum:question_detail', pk=question.pk)

@login_required
def vote_answer(request, pk):
    """Voter pour une réponse"""
    answer = get_object_or_404(Answer, pk=pk)
    question = answer.question
    
    if request.method == 'POST':
        vote_type = request.POST.get('vote_type', 'up')  # up ou down
        
        # Debug
        print(f"DEBUG: vote_type = {vote_type}")
        print(f"DEBUG: user = {request.user}")
        print(f"DEBUG: answer = {answer}")
        
        # Vérifier si l'utilisateur a déjà voté
        existing_vote = Vote.objects.filter(user=request.user, answer=answer).first()
        print(f"DEBUG: existing_vote = {existing_vote}")
        
        if existing_vote:
            # Si le vote est le même, l'annuler
            if existing_vote.vote_type == vote_type:
                existing_vote.delete()
                messages.info(request, 'Votre vote a été annulé.')
            else:
                # Sinon, changer le type de vote
                existing_vote.vote_type = vote_type
                existing_vote.save()
                messages.success(request, 'Votre vote a été mis à jour !')
        else:
            try:
                # Créer le nouveau vote
                vote = Vote.objects.create(user=request.user, answer=answer, vote_type=vote_type)
                print(f"DEBUG: vote créé = {vote}")
                messages.success(request, 'Votre vote a été enregistré !')
            except Exception as e:
                print(f"DEBUG: Erreur création vote = {e}")
                messages.error(request, f'Erreur lors du vote: {e}')
        
        # Vérifier le nombre de votes après création
        total_votes = Vote.objects.filter(answer=answer).count()
        print(f"DEBUG: Total votes après = {total_votes}")
        
        return redirect('forum:question_detail', pk=question.pk)

@login_required
def validate_answer(request, pk):
    """Valider une réponse (formateur/admin uniquement)"""
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, 'Vous n\'avez pas les permissions pour valider des réponses.')
        return redirect('forum:question_detail', pk=pk)
    
    answer = get_object_or_404(Answer, pk=pk)
    question = answer.question
    
    if request.method == 'POST':
        form = ValidationForm(request.POST)
        if form.is_valid():
            # Marquer la réponse comme validée
            answer.is_validated = True
            answer.validated_by = request.user
            answer.validated_at = timezone.now()
            answer.save(update_fields=['is_validated', 'validated_by', 'validated_at'])
            
            # Marquer la question comme résolue si nécessaire
            if form.cleaned_data['validation_reason'] == 'correct':
                question.is_closed = True
                question.save(update_fields=['is_closed'])
            
            messages.success(request, 'Réponse validée avec succès !')
        else:
            form = ValidationForm()
    
    return render(request, 'forum/validate_answer.html', {
        'question': question,
        'answer': answer,
        'form': form
    })

@login_required
def close_question(request, pk):
    """Fermer une question"""
    question = get_object_or_404(Question, pk=pk)
    
    # Seul l'auteur ou un admin peut fermer une question
    if question.author != request.user and not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Vous n'avez pas la permission de fermer cette question.")
        return redirect('forum:question_detail', pk=pk)
    
    if request.method == 'POST':
        question.is_closed = True
        question.save()
        messages.success(request, 'La question a été fermée avec succès.')
    
    return redirect('forum:question_detail', pk=pk)

@login_required
def delete_question(request, pk):
    """Supprimer une question"""
    question = get_object_or_404(Question, pk=pk)
    
    # Seul l'auteur ou un admin peut supprimer une question
    if question.author != request.user and not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Vous n'avez pas la permission de supprimer cette question.")
        return redirect('forum:question_detail', pk=pk)
    
    if request.method == 'POST':
        title = question.title  # Garder le titre pour le message
        question.delete()
        messages.success(request, f'La question "{title}" a été supprimée avec succès.')
        return redirect('forum:home')
    
    return render(request, 'forum/delete_question.html', {
        'question': question
    })

@login_required
def comment_answer(request, answer_id):
    """Ajouter un commentaire à une réponse"""
    answer = get_object_or_404(Answer, pk=answer_id)
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            comment = Comment.objects.create(
                author=request.user,
                answer=answer,
                content=content
            )
            messages.success(request, 'Votre commentaire a été ajouté avec succès.')
        else:
            messages.error(request, 'Le contenu du commentaire ne peut pas être vide.')
    
    return redirect('forum:question_detail', pk=answer.question.id)

@login_required
def delete_answer(request, pk):
    """Supprimer une réponse"""
    answer = get_object_or_404(Answer, pk=pk)
    question = answer.question
    
    # Seul l'auteur de la réponse ou un admin peut supprimer
    if answer.author != request.user and not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Vous n'avez pas la permission de supprimer cette réponse.")
        return redirect('forum:question_detail', pk=question.pk)
    
    if request.method == 'POST':
        answer.delete()
        messages.success(request, 'La réponse a été supprimée avec succès.')
        return redirect('forum:question_detail', pk=question.pk)
    
    return render(request, 'forum/delete_answer.html', {
        'answer': answer,
        'question': question
    })
