from django.contrib import admin
from .models import Payment, ModuleAccess, PaymentPlan, Subscription

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'module', 'amount', 'status', 'payment_method', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['user__username', 'module__title', 'transaction_id']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['-created_at']

@admin.register(ModuleAccess)
class ModuleAccessAdmin(admin.ModelAdmin):
    list_display = ['user', 'module', 'payment', 'granted_at', 'expires_at', 'is_active']
    list_filter = ['is_active', 'granted_at', 'expires_at']
    search_fields = ['user__username', 'module__title']
    ordering = ['-granted_at']

@admin.register(PaymentPlan)
class PaymentPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'duration_days', 'max_modules', 'is_active']
    list_filter = ['is_active', 'duration_days']
    search_fields = ['name', 'description']
    ordering = ['price']

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'started_at', 'expires_at', 'is_active']
    list_filter = ['is_active', 'started_at', 'expires_at', 'plan']
    search_fields = ['user__username', 'plan__name']
    ordering = ['-started_at']
