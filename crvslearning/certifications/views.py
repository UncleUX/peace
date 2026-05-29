"""
Vues pour la gestion des certifications
"""

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from .models import Certification
from .utils import get_user_certifications, get_certification_stats, create_certification_pdf, generate_certificate_pdf_unified


class CertificationListView(LoginRequiredMixin, ListView):
    """Liste des certifications de l'utilisateur"""
    model = Certification
    template_name = 'certifications/certification_list.html'
    context_object_name = 'certifications'
    paginate_by = 10
    
    def get_queryset(self):
        return get_user_certifications(self.request.user)


class CertificationDetailView(LoginRequiredMixin, DetailView):
    """Détail d'une certification"""
    model = Certification
    template_name = 'certifications/certification_detail.html'
    context_object_name = 'certification'
    
    def get_queryset(self):
        return Certification.objects.filter(
            user=self.request.user, 
            is_valid=True
        )


@login_required
def certification_dashboard(request):
    """Tableau de bord des certifications"""
    user = request.user
    certifications = get_user_certifications(user)
    stats = get_certification_stats(user)
    
    context = {
        'certifications': certifications[:5],  # 5 plus récentes
        'stats': stats,
        'total_certifications': stats['total_certifications'],
        'latest_certification': stats['latest'],
        'certifications_by_level': stats['by_level'],
    }
    
    return render(request, 'certifications/certification_dashboard.html', context)


@login_required
def download_by_code(request, code):
    """Télécharger une certification par son code"""
    certification = get_object_or_404(
        Certification, 
        code=code, 
        user=request.user, 
        is_valid=True
    )
    
    # Utiliser la fonction unifiée
    pdf_buffer = generate_certificate_pdf_unified(certification)
    
    response = HttpResponse(
        pdf_buffer.getvalue(),
        content_type='application/pdf'
    )
    response['Content-Disposition'] = f'attachment; filename="certification_{certification.code}.pdf"'
    
    return response


@login_required
def download_certification(request, certification_id):
    """Télécharger une certification en PDF"""
    certification = get_object_or_404(
        Certification, 
        id=certification_id, 
        user=request.user, 
        is_valid=True
    )
    
    # Utiliser la fonction unifiée
    pdf_buffer = generate_certificate_pdf_unified(certification)
    
    response = HttpResponse(
        pdf_buffer.getvalue(),
        content_type='application/pdf'
    )
    response['Content-Disposition'] = f'attachment; filename="certification_{certification.code}.pdf"'
    
    return response


@login_required
def verify(request, code):
    """Vérifier la validité d'une certification"""
    cert = get_object_or_404(Certification, code=code)
    return render(request, 'certifications/verify.html', {
        'cert': cert,
    })


@login_required
def achievements(request):
    """Affiche la page des réalisations avec les badges de certification de l'utilisateur."""
    # Récupérer toutes les certifications valides (parcours ET évaluations)
    certifications = Certification.objects.filter(
        user=request.user, 
        is_valid=True
    ).prefetch_related('course', 'template').order_by('-issued_at')
    
    # Grouper les certifications par niveau
    certifications_by_level = {
        'beginner': certifications.filter(level='beginner'),
        'intermediate': certifications.filter(level='intermediate'),
        'advanced': certifications.filter(level='advanced'),
    }
    
    context = {
        'certifications': certifications,
        'certifications_by_level': certifications_by_level,
        'total_certifications': certifications.count(),
        'latest_certification': certifications.first() if certifications.exists() else None,
    }
    
    return render(request, 'certifications/achievements.html', context)
