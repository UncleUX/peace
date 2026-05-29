from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
import uuid

from courses.models import Module, Lesson
from .models import Payment, ModuleAccess, PaymentPlan, Subscription
from .forms import PaymentForm


class ModulePaymentView(LoginRequiredMixin, DetailView):
    """Vue pour afficher les détails de paiement d'un module"""
    model = Module
    template_name = 'payments/module_payment.html'
    context_object_name = 'module'
    pk_url_kwarg = 'module_id'  # Utiliser module_id au lieu de pk
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        module = self.get_object()
        
        # Vérifier si l'utilisateur a déjà accès à ce module
        has_access = ModuleAccess.objects.filter(
            user=self.request.user,
            module=module
        ).first()
        
        # Vérifier si l'utilisateur a déjà un paiement en cours
        pending_payment = Payment.objects.filter(
            user=self.request.user,
            module=module,
            status='pending'
        ).first()
        
        context.update({
            'has_access': has_access,
            'pending_payment': pending_payment,
            'payment_plans': PaymentPlan.objects.filter(is_active=True),
        })
        
        return context


@login_required
@require_POST
def initiate_payment(request, module_id):
    """Initier un paiement pour un module"""
    module = get_object_or_404(Module, id=module_id)
    
    if not module.is_paid:
        messages.error(request, "Ce module n'est pas payant.")
        return redirect('courses:module_detail', course_id=module.course.id, module_id=module_id)
    
    # Vérifier si l'utilisateur a déjà accès
    existing_access = ModuleAccess.objects.filter(
        user=request.user,
        module=module
    ).first()
    
    if existing_access and existing_access.is_valid:
        messages.info(request, "Vous avez déjà accès à ce module.")
        return redirect('courses:module_detail', course_id=module.course.id, module_id=module_id)
    
    # Vérifier si un paiement est déjà en cours
    pending_payment = Payment.objects.filter(
        user=request.user,
        module=module,
        status='pending'
    ).first()
    
    if pending_payment:
        messages.info(request, "Vous avez déjà un paiement en cours pour ce module.")
        return redirect('payments:payment_detail', pk=pending_payment.id)
    
    # Créer un nouveau paiement
    payment = Payment.objects.create(
        user=request.user,
        module=module,
        amount=module.price,
        status='pending',
        transaction_id=str(uuid.uuid4())
    )
    
    messages.success(request, "Paiement initié avec succès. Veuillez procéder au paiement.")
    return redirect('payments:payment_detail', pk=payment.id)


class PaymentDetailView(LoginRequiredMixin, DetailView):
    """Vue pour afficher les détails d'un paiement"""
    model = Payment
    template_name = 'payments/payment_detail.html'
    context_object_name = 'payment'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        payment = self.get_object()
        
        # Ajouter les informations de paiement simulé
        context.update({
            'payment_methods': [
                {'id': 'orange_money', 'name': 'Orange Money', 'icon': '📱'},
                {'id': 'mtn_money', 'name': 'MTN Mobile Money', 'icon': '📱'},
                {'id': 'card', 'name': 'Carte bancaire', 'icon': '💳'},
            ]
        })
        
        return context


@login_required
@require_POST
def process_payment(request, payment_id):
    """Traiter le paiement (simulation)"""
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    
    if payment.status != 'pending':
        messages.error(request, "Ce paiement a déjà été traité.")
        return redirect('payments:payment_detail', pk=payment_id)
    
    payment_method = request.POST.get('payment_method')
    phone_number = request.POST.get('phone_number')
    
    if not payment_method or not phone_number:
        messages.error(request, "Veuillez remplir tous les champs.")
        return redirect('payments:payment_detail', pk=payment_id)
    
    # Simulation du traitement de paiement
    # Dans un vrai projet, vous intégreriez ici l'API du fournisseur de paiement
    import random
    success = random.choice([True, True, True, False])  # 75% de succès pour la démo
    
    if success:
        # Mettre à jour le paiement
        payment.status = 'completed'
        payment.payment_method = payment_method
        payment.transaction_id = f"TXN{uuid.uuid4().hex[:12].upper()}"
        payment.save()
        
        # Créer l'accès au module (vérifier s'il n'existe pas déjà)
        module_access, created = ModuleAccess.objects.get_or_create(
            user=request.user,
            module=payment.module,
            defaults={
                'payment': payment,
                'expires_at': None  # Accès permanent
            }
        )
        
        if created:
            messages.success(request, 
                f"Paiement de {payment.amount} FCFA effectué avec succès ! "
                f"Vous avez maintenant accès au module '{payment.module.title}'."
            )
        else:
            messages.info(request, 
                f"Paiement de {payment.amount} FCFA effectué avec succès ! "
                f"Vous aviez déjà accès au module '{payment.module.title}'."
            )
        return redirect('courses:module_detail', course_id=payment.module.course.id, module_id=payment.module.id)
    else:
        payment.status = 'failed'
        payment.save()
        messages.error(request, "Le paiement a échoué. Veuillez réessayer.")
        return redirect('payments:payment_detail', pk=payment_id)


class PaymentHistoryView(LoginRequiredMixin, ListView):
    """Vue pour afficher l'historique des paiements de l'utilisateur"""
    model = Payment
    template_name = 'payments/payment_history.html'
    context_object_name = 'payments'
    paginate_by = 10
    
    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user).order_by('-created_at')


class MyAccessView(LoginRequiredMixin, ListView):
    """Vue pour afficher les accès aux modules de l'utilisateur"""
    model = ModuleAccess
    template_name = 'payments/my_access.html'
    context_object_name = 'accesses'
    paginate_by = 10
    
    def get_queryset(self):
        return ModuleAccess.objects.filter(
            user=self.request.user
        ).select_related('module', 'module__course', 'payment').order_by('-granted_at')


@login_required
def check_module_access(request, module_id):
    """Vérifier si l'utilisateur a accès à un module (API endpoint)"""
    module = get_object_or_404(Module, id=module_id)
    
    has_access = False
    access_type = 'free'
    
    if module.is_paid:
        access = ModuleAccess.objects.filter(
            user=request.user,
            module=module
        ).first()
        
        if access and access.is_valid:
            has_access = True
            access_type = 'paid'
    else:
        has_access = True
        access_type = 'free'
    
    return JsonResponse({
        'has_access': has_access,
        'access_type': access_type,
        'module_title': module.title,
        'is_paid': module.is_paid,
        'price': float(module.price) if module.is_paid else 0
    })


@login_required
@require_POST
def extend_subscription(request, subscription_id):
    """Prolonger un abonnement"""
    subscription = get_object_or_404(Subscription, id=subscription_id, user=request.user)
    
    # Pour la démo, on ajoute 30 jours
    subscription.extend(30)
    
    messages.success(request, "Votre abonnement a été prolongé de 30 jours.")
    return redirect('payments:my_access')
