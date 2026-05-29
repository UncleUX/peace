from django.urls import path
from . import views

app_name = 'certifications'

urlpatterns = [
    path('verify/<str:code>/', views.verify, name='verify'),
    path('download/<str:code>/', views.download_by_code, name='download'),
    path('download-id/<int:certification_id>/', views.download_certification, name='download_id'),
    path('achievements/', views.achievements, name='achievements'),
]
