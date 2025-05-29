from django.urls import path
from . import views

app_name = 'audits'

urlpatterns = [
    path('audits/', views.audits_home, name='audits_home'),
    path('annual-audit-program/', views.annual_audit_program, name='annual_audit_program'), 
    path('annual-audit-plan/', views.annual_audit_plan, name='annual_audit_plan'),  
    path('conduct-internal-audits/', views.conduct_internal_audits, name='conduct_internal_audits'),  
    path('add_audit_program_header/', views.add_audit_program_header, name='add_audit_program_header'),
    path('add_annual_program/', views.add_annual_program, name='add_annual_program'),
    path('add_annual_plan/', views.add_annual_plan, name='add_annual_plan'),
    path('add_annual_program_user/', views.add_annual_program_user, name='add_annual_program_user'),
    path('add_annual_plan_auditor/', views.add_annual_plan_auditor, name='add_annual_plan_auditor'),
    path('add_annual_plan_audited/', views.add_annual_plan_audited, name='add_annual_plan_audited'),
    path('add_checklist/', views.add_checklist, name='add_checklist'),
    path('add_findings/', views.add_findings, name='add_findings'),
    path('add_audit_report/', views.add_audit_report, name='add_audit_report'),
    path('add_process_requirement/', views.add_process_requirement, name='add_process_requirement'),
    path('add_audited_evaluation_question/', views.add_audited_evaluation_question, name='add_audited_evaluation_question'),
    path('add_auditor_evaluation/', views.add_auditor_evaluation, name='add_auditor_evaluation'),
    path('add_lead_auditor_evaluation_question/', views.add_lead_auditor_evaluation_question, name='add_lead_auditor_evaluation_question'),

]
