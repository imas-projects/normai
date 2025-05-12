# audits/urls.py
from django.urls import path
from . import views

app_name = 'audits'

urlpatterns = [
    path('audits/', views.audits_home, name='audits_home'),
    path('annual-audit-program/', views.annual_audit_program, name='annual_program'), 
    path('annual-audit-plan/', views.annual_audit_plan, name='annual_plan'),  
    path('conduct-internal-audits/', views.conduct_internal_audits, name='conduct_audit'),

    # Formularios para agregar datos
    path('add-audited/', views.add_audited, name='add_audited'),
    path('add-audited-evaluation-question/', views.add_audited_evaluation_question, name='add_audited_evaluation_question'),
    path('add-lead-auditor-evaluation-question/', views.add_lead_auditor_evaluation_question, name='add_lead_auditor_evaluation_question'),
    path('add-audit-program-header/', views.add_audit_program_header, name='add_audit_program_header'),
    path('add-annual-program/', views.add_annual_program, name='add_annual_program'),
    path('add-audit-plan-header/', views.add_audit_plan_header, name='add_audit_plan_header'),
    path('add-associated-elements/', views.add_associated_elements, name='add_associated_elements'),
    path('add-findings/', views.add_findings, name='add_findings'),
    path('add-audit-report/', views.add_audit_report, name='add_audit_report'),
    path('add-requirement/', views.add_requirement, name='add_requirement'),
    path('add-checklist/', views.add_checklist, name='add_checklist'),

    # Endpoints para obtener datos dinámicamente (AJAX)
    path('get_checklist_data/<int:requirement_id>/', views.get_checklist_data, name='get_checklist_data'),
    path('get-audited-questions/<int:requirement_id>/', views.get_audited_questions, name='get_audited_questions'),
    path('get-lead-auditor-questions/<int:requirement_id>/', views.get_lead_auditor_questions, name='get_lead_auditor_questions'),
]

