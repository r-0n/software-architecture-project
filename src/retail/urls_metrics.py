"""
URL configuration for metrics and observability endpoints.
"""
from django.urls import path
from . import views

app_name = 'metrics'

urlpatterns = [
    path('dashboard/', views.metrics_dashboard, name='dashboard'),
    path('quality-scenarios/', views.quality_scenarios_verification, name='quality_scenarios'),
    path('api/', views.metrics_api, name='api'),
]

