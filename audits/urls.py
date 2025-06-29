from django.urls import path
from . import views

app_name = 'audits'

urlpatterns = [
    path('audits/', views.audits_home, name='audits_home'),
    path('annual-audit-program/', views.annual_audit_program, name='annual_audit_program'), 
    path('annual-audit-plan/', views.annual_audit_plan, name='annual_audit_plan'),  
    path('conduct-internal-audits/', views.conduct_internal_audits, name='conduct_internal_audits'),  
    path('add_audit_program_header/', views.add_audit_program_header, name='add_audit_program_header'),
    path('suggest_audit_program_fields/', views.suggest_audit_program_fields, name='suggest_audit_program_fields'),
    path('add_annual_program/', views.add_annual_program, name='add_annual_program'),
    path('suggest-annual-program-processes/', views.suggest_annual_program_processes_view, name='suggest_annual_program_processes'),
    path('save-annual-program-suggestion/', views.save_selected_annual_program_process, name='save_annual_program_suggestion'),
    path('add_annual_plan/', views.add_annual_plan, name='add_annual_plan'),
    path('add_annual_plan_auditor/', views.add_annual_plan_auditor, name='add_annual_plan_auditor'),
    path('suggest-auditor/', views.suggest_auditor_view, name='suggest_auditor'),
    path('save-selected-auditor/', views.save_selected_auditor, name='save_selected_auditor'),
    path('add_annual_plan_audited/', views.add_annual_plan_audited, name='add_annual_plan_audited'),
    path('add_checklist/', views.add_checklist, name='add_checklist'),
    path('add_findings/', views.add_findings, name='add_findings'),
    path('classify-finding/', views.classify_finding_view, name='classify_finding'),
    path('add_audit_report/', views.add_audit_report, name='add_audit_report'),
    path('suggest_audit_report/', views.suggest_audit_report_view, name='suggest_audit_report'),
    path('add_process_requirement/', views.add_process_requirement, name='add_process_requirement'),
    path('add_audited_evaluation_question/', views.add_audited_evaluation_question, name='add_audited_evaluation_question'),
    path('suggest-audit-questions/', views.suggest_audit_questions_view, name='suggest_audit_questions'),
    path("save-audit-question/", views.save_selected_audit_question, name="save_audit_question"),
    path('add_auditor_evaluation/', views.add_auditor_evaluation, name='add_auditor_evaluation'),
    path("suggest-compliance-rate/", views.suggest_compliance_rate_view, name="suggest_compliance_rate"),
    path('add_lead_auditor_evaluation_question/', views.add_lead_auditor_evaluation_question, name='add_lead_auditor_evaluation_question'),
    path('add_corrective_action/', views.add_corrective_action, name='add_corrective_action'),
    path('add_corrective_action_followup/', views.add_corrective_action_followup, name='add_corrective_action_followup'),
]
