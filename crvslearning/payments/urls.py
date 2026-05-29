from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # Paiement de module
    path('module/<int:module_id>/payment/', views.ModulePaymentView.as_view(), name='module_payment'),
    path('initiate/<int:module_id>/', views.initiate_payment, name='initiate_payment'),
    path('payment/<uuid:pk>/', views.PaymentDetailView.as_view(), name='payment_detail'),
    path('process/<uuid:payment_id>/', views.process_payment, name='process_payment'),
    
    # Historique et accès
    path('history/', views.PaymentHistoryView.as_view(), name='payment_history'),
    path('my-access/', views.MyAccessView.as_view(), name='my_access'),
    
    # API endpoints
    path('check-access/<int:module_id>/', views.check_module_access, name='check_module_access'),
    
    # Abonnements
    path('extend/<int:subscription_id>/', views.extend_subscription, name='extend_subscription'),
]
