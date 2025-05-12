from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from collections import defaultdict, OrderedDict
from datetime import datetime

from .forms import (
    AuditedForm, AuditedEvaluationQuestionForm, 
    LeadAuditorEvaluationQuestionForm, AuditProgramHeaderForm, 
    AnnualProgramForm, AuditPlanHeaderForm, AssociatedElementsForm, 
    FindingsForm, AuditReportForm, UnifiedRequirementForm, ChecklistForm
)

from .models import (
    Audited, AuditProgramHeader, AuditPlanHeader, AnnualProgram, 
    AssociatedElements, Checklist, UnifiedRequirement, AuditReport, Findings, 
    AuditedEvaluationQuestion, LeadAuditorEvaluationQuestion
)

# === BASIC VIEWS ===

def audits_home(request):
    return render(request, 'mistemplates/audits.html')

# === ANNUAL AUDIT PROGRAM ===

def annual_audit_program(request):
    audit_headers = AuditProgramHeader.objects.all()

    today = datetime.today()
    start_month = today.month - 1 if today.month > 1 else 12
    start_year = today.year if today.month > 1 else today.year - 1
    month_range = [(start_year, start_month)]
    for _ in range(11):
        y, m = month_range[-1]
        next_month = (m % 12) + 1
        next_year = y + (1 if next_month == 1 else 0)
        month_range.append((next_year, next_month))

    annual_programs = AnnualProgram.objects.filter(
        year__in={y for y, _ in month_range},
        month__in={m for _, m in month_range}
    ).order_by('year', 'month')

    annual_programs_by_year = OrderedDict()
    for y, m in month_range:
        month_name = datetime(y, m, 1).strftime('%B')
        if y not in annual_programs_by_year:
            annual_programs_by_year[y] = OrderedDict()
        annual_programs_by_year[y][month_name] = annual_programs.filter(year=y, month=m)

    if request.method == "POST":
        if "save_header" in request.POST:
            form = AuditProgramHeaderForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect('audits:annual_audit_program')
    else:
        form = AuditProgramHeaderForm()

    return render(request, 'mistemplates/annual_audit_program.html', {
        'audit_headers': audit_headers,
        'header_form': form,
        'annual_programs_by_year': annual_programs_by_year,
    })

# === ANNUAL AUDIT PLAN ===

def annual_audit_plan(request):
    audit_headers = AuditProgramHeader.objects.all()
    audit_plans = AuditPlanHeader.objects.all()
    audited_people = Audited.objects.select_related('audited_user', 'requirement')

    audit_data = []
    for audited in audited_people:
        elements = AssociatedElements.objects.filter(requirement=audited.requirement).first()
        audit_data.append({
            'requirement': audited.requirement,
            'audited_person': audited.audited_user,
            'audit_date': elements.audit_date if elements else None,
            'audit_time': elements.audit_time if elements else None,
            'audit_team_member': elements.audit_team_member if elements else None,
            'audit_location': elements.audit_location if elements else None,
        })

    return render(request, 'mistemplates/annual_audit_plan.html', {
        'audit_headers': audit_headers,
        'audit_plans': audit_plans,
        'audit_data': audit_data,
    })

# === CONDUCT INTERNAL AUDITS ===

def conduct_internal_audits(request):
    audited_list = Audited.objects.select_related("requirement", "audited_user")
    associated_elements = AssociatedElements.objects.select_related("requirement", "audit_team_member__person")

    audit_data = []
    for audited in audited_list:
        req = audited.requirement
        entry = {
            "requirement": req.name if req else "N/A",
            "requirement_id": req.id if req else None,
            "audited": f"{audited.audited_user.get_full_name()}",
            "auditor": "N/A",
            "findings": [],
            "audit_report": None
        }

        element = associated_elements.filter(requirement=req).first()
        if element:
            auditor = element.audit_team_member.person
            entry["auditor"] = f"{auditor.get_full_name()}"

        if req:
            entry["findings"] = [
                {"finding_text": f.finding_text, "classification": f.classification}
                for f in Findings.objects.filter(requirement=req)
            ]
            report = AuditReport.objects.filter(requirement=req).first()
            if report:
                entry["audit_report"] = {"summary": report.summary, "strengths": report.strengths}

        audit_data.append(entry)

    return render(request, "mistemplates/conduct_internal_audits.html", {"audit_data": audit_data})

'''
# === ADD VIEWS ===

def add_audited(request):
    return _add_form_view(request, AuditedForm, 'audits:audits_home', 'add_audited.html', use_cleaned_user=True)

def add_checklist_question(request):
    return _add_form_view(request, ChecklistForm, 'audits:conduct_audit', 'add_checklist_question.html')

def add_audited_evaluation_question(request):
    return _add_form_view(request, AuditedEvaluationQuestionForm, 'audits:conduct_audit', 'add_audited_evaluation_question.html')

def add_lead_auditor_evaluation_question(request):
    return _add_form_view(request, LeadAuditorEvaluationQuestionForm, 'audits:conduct_audit', 'add_lead_auditor_evaluation_question.html')

def add_audit_program_header(request):
    return _add_form_view(request, AuditProgramHeaderForm, 'audits:annual_program', 'add_audit_program_header.html')

def add_annual_program(request):
    return _add_form_view(request, AnnualProgramForm, 'audits:annual_program', 'add_annual_program.html')

def add_audit_plan_header(request):
    return _add_form_view(request, AuditPlanHeaderForm, 'audits:annual_plan', 'add_audit_plan_header.html')

def add_associated_elements(request):
    return _add_form_view(request, AssociatedElementsForm, 'audits:annual_plan', 'add_associated_elements.html')

def add_findings(request):
    return _add_form_view(request, FindingsForm, 'audits:conduct_audit', 'add_findings.html')

def add_audit_report(request):
    return _add_form_view(request, AuditReportForm, 'audits:conduct_audit', 'add_audit_report.html')

def add_requirement(request):
    return _add_form_view(request, UnifiedRequirementForm, 'audits:audits_home', 'add_requirement.html')

def add_checklist(request):
    if request.method == "POST":
        form = ChecklistForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('audits:conduct_audit')
        else:
            return JsonResponse({"status": "error", "errors": form.errors}, status=400)
    return render(request, "mistemplates/add_checklist.html", {"form": ChecklistForm()})

# === AJAX VIEWS ===

def get_checklist_data(request, requirement_id):
    data = list(Checklist.objects.filter(requirement_id=requirement_id).order_by('orden').values(
        'id', 'question_text', 'orden', 'evidence', 'compliance'
    ))
    return JsonResponse(data, safe=False)

def get_audited_questions(request, requirement_id):
    data = list(AuditedEvaluationQuestion.objects.filter(requirement_id=requirement_id).order_by('orden').values(
        'id', 'question_text', 'orden', 'rate'
    ))
    return JsonResponse(data, safe=False)

def get_lead_auditor_questions(request, requirement_id):
    data = list(LeadAuditorEvaluationQuestion.objects.filter(requirement_id=requirement_id).order_by('orden').values(
        'id', 'question_text', 'orden', 'rate'
    ))
    return JsonResponse(data, safe=False)

# === HELPER FUNCTION ===

def _add_form_view(request, form_class, success_url_name, template_name, use_cleaned_user=False):
    if request.method == 'POST':
        form = form_class(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
            if use_cleaned_user:
                instance.audited_user = form.cleaned_data['audited_user']
            instance.save()
            return redirect(success_url_name)
    else:
        form = form_class()
    return render(request, f'mistemplates/{template_name}', {'form': form})
'''
