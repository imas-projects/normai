from django.urls import path
from . import views

app_name = 'demo'

urlpatterns = [
    path('dashboard/', views.demo_dashboard, name='demo_dashboard'),
    path('normativo/', views.demo_normative_catalog, name='demo_normative_catalog'),
    path('auditorias/', views.demo_audit_checklists, name='demo_audit_checklists'),
    path('cumplimiento/', views.demo_compliance, name='demo_compliance'),
    path('analitica/', views.demo_analytics, name='demo_analytics'),
]