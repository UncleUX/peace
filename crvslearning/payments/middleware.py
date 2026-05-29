from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from courses.models import Module
from .models import ModuleAccess


class ModuleAccessMixin:
    """Mixin pour vérifier l'accès aux modules"""
    
    def dispatch(self, request, *args, **kwargs):
        module_id = kwargs.get('module_id') or kwargs.get('pk')
        
        if module_id:
            module = get_object_or_404(Module, id=module_id)
            
            # Si le module est payant, vérifier l'accès
            if module.is_paid:
                access = ModuleAccess.objects.filter(
                    user=request.user,
                    module=module
                ).first()
                
                if not access or not access.is_valid:
                    messages.error(
                        request, 
                        f"Ce module est payant. Vous devez payer {module.price} FCFA pour y accéder."
                    )
                    return redirect('payments:module_payment', module_id=module.id)
        
        return super().dispatch(request, *args, **kwargs)


class CanAccessModule(UserPassesTestMixin):
    """Mixin pour vérifier si l'utilisateur peut accéder à un module"""
    
    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
        
        module_id = self.kwargs.get('module_id') or self.kwargs.get('pk')
        if not module_id:
            return False
        
        module = get_object_or_404(Module, id=module_id)
        
        # Si le module n'est pas payant, accès autorisé
        if not module.is_paid:
            return True
        
        # Vérifier si l'utilisateur a un accès valide
        access = ModuleAccess.objects.filter(
            user=self.request.user,
            module=module
        ).first()
        
        return access and access.is_valid
    
    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect('users:login')
        
        module_id = self.kwargs.get('module_id') or self.kwargs.get('pk')
        module = get_object_or_404(Module, id=module_id)
        
        if module.is_paid:
            messages.error(
                self.request,
                f"Ce module est payant. Vous devez payer {module.price} FCFA pour y accéder."
            )
            return redirect('payments:module_payment', module_id=module.id)
        
        return redirect('courses:module_detail', course_id=module.course.id, module_id=module.id)


def check_module_access_view(view_func):
    """Décorateur pour vérifier l'accès aux modules"""
    def wrapper(request, *args, **kwargs):
        module_id = kwargs.get('module_id') or kwargs.get('pk')
        
        if module_id and request.user.is_authenticated:
            module = get_object_or_404(Module, id=module_id)
            
            if module.is_paid:
                access = ModuleAccess.objects.filter(
                    user=request.user,
                    module=module
                ).first()
                
                if not access or not access.is_valid:
                    messages.error(
                        request,
                        f"Ce module est payant. Vous devez payer {module.price} FCFA pour y accéder."
                    )
                    return redirect('payments:module_payment', module_id=module.id)
        
        return view_func(request, *args, **kwargs)
    
    return wrapper
