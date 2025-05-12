from django.urls import path
from . import views

app_name = 'audits'

urlpatterns = [
    # Página principal de auditorías
    path('audits/', views.audits_home, name='audits_home'),

    # Páginas de los programas de auditoría
    path('annual-audit-program/', views.annual_audit_program, name='annual_audit_program'), 
    path('annual-audit-plan/', views.annual_audit_plan, name='annual_audit_plan'),  
    path('conduct-internal-audits/', views.conduct_internal_audits, name='conduct_internal_audits'),  
]
