'''
from django.urls import path
from . import views
from .views import audits_home, annual_audit_program, annual_audit_plan, conduct_internal_audits, add_audit_team, add_audited, add_audited_evaluation_question
from .views import add_lead_auditor_evaluation_question, add_audit_program_header, add_annual_program, add_audit_plan_header, add_associated_elements, add_findings, add_audit_report
from .views import add_requirement, add_checklist, get_checklist_data, get_audited_questions, get_lead_auditor_questions


app_name = 'audits'

urlpatterns = [
    path('audits/', audits_home, name='audits_home'),
    path('annual-audit-program/', annual_audit_program, name='annual_program'), 
    path('annual-audit-plan/', annual_audit_plan, name='annual_plan'),  
    path('conduct-internal-audits/', conduct_internal_audits, name='conduct_audit'),
    path('add-audit-team/', add_audit_team, name='add_audit_team'),
    path('add-audited/', add_audited, name='add_audited'),
    path('add-audited-evaluation-question/', add_audited_evaluation_question, name='add_audited_evaluation_question'),
    path('add-lead-auditor-evaluation-question/', add_lead_auditor_evaluation_question, name='add_lead_auditor_evaluation_question'),
    path('add-audit-program-header/', add_audit_program_header, name='add_audit_program_header'),
    path('add-annual-program/', add_annual_program, name='add_annual_program'),
    path('add-audit-plan-header/', add_audit_plan_header, name='add_audit_plan_header'),
    path('add-associated-elements/', add_associated_elements, name='add_associated_elements'),
    path('add-findings/', add_findings, name='add_findings'),
    path('add-audit-report/', add_audit_report, name='add_audit_report'),
    path('add-requirement/', add_requirement, name='add_requirement'),
    path("add-checklist/", add_checklist, name="add_checklist"),
    path('get_checklist_data/<int:requirement_id>/', get_checklist_data, name='get_checklist_data'),
    path('get-audited-questions/<int:requirement_id>/', get_audited_questions, name='get_audited_questions'),
    path('get-lead-auditor-questions/<int:requirement_id>/', get_lead_auditor_questions, name='get_lead_auditor_questions'),
]
'''
