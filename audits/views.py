from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from collections import defaultdict, OrderedDict
from datetime import datetime

'''
from .forms import (
    AuditedForm, AuditedEvaluationQuestionForm, 
    LeadAuditorEvaluationQuestionForm, AuditProgramHeaderForm, 
    AnnualProgramForm, AuditPlanHeaderForm, AssociatedElementsForm, 
    FindingsForm, AuditReportForm, UnifiedRequirementForm, ChecklistForm
)
'''

from .models import (
    AuditProgramHeader,ProcessRequirement, AnnualProgram, AnnualProgramUser, 
    AnnualPlan,
    Checklist,
    AuditReport,
    Findings,
    AuditedEvaluationQuestion,
    LeadAuditorEvaluationQuestion
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
        program_header__year__in={y for y, _ in month_range},
        month__in={m for _, m in month_range}
    ).select_related("program_header", "process").order_by('program_header__year', 'month')

    program_ids = annual_programs.values_list("id", flat=True)

    users_by_program = defaultdict(list)
    for apu in AnnualProgramUser.objects.filter(annual_program_id__in=program_ids).select_related("user"):
        users_by_program[apu.annual_program_id].append(apu.user)

    requirements_by_process = defaultdict(list)
    for pr in ProcessRequirement.objects.select_related("process", "requirement"):
        requirements_by_process[pr.process_id].append(pr.requirement)

    annual_programs_by_year = OrderedDict()
    
    all_users = User.objects.all()

    for y, m in month_range:
        month_name = datetime(y, m, 1).strftime('%B')
        if y not in annual_programs_by_year:
            annual_programs_by_year[y] = OrderedDict()

        filtered = annual_programs.filter(program_header__year=y, month=m)
        enriched_programs = []

        for program in filtered:
            enriched_programs.append({
                "program": program,
                "users": users_by_program.get(program.id, []),
                "requirements": requirements_by_process.get(program.process_id, [])
            })

        annual_programs_by_year[y][month_name] = enriched_programs

    return render(request, 'mistemplates/annual_audit_program.html', {
        'audit_headers': audit_headers,
        'annual_programs_by_year': annual_programs_by_year,
        'users': all_users,
    })

# === ANNUAL AUDIT PLAN ===

def annual_audit_plan(request):
    plans = AnnualPlan.objects.select_related(
        "annual_program__program_header",
        "annual_program__process",
        "lider"
    ).prefetch_related(
        "auditors__user",
        "audited_users__user"
    )

    audit_data = []
    for plan in plans:
        audit_data.append({
            "plan_id": plan.id,
            "process": plan.annual_program.process.name if plan.annual_program and plan.annual_program.process else None,
            "year": plan.annual_program.program_header.year if plan.annual_program and plan.annual_program.program_header else None,
            "month": plan.annual_program.month if plan.annual_program else None,
            "lider": plan.lider.get_full_name() if plan.lider else "No leader assigned",
            "audit_opening_date": plan.audit_opening_date,
            "audit_closing_date": plan.audit_closing_date,
            "audit_opening_location": plan.audit_opening_location,
            "audit_closing_location": plan.audit_closing_location,
            "auditors": [auditor.user.get_full_name() for auditor in plan.auditors.all()],
            "audited_users": [audited.user.get_full_name() for audited in plan.audited_users.all()],
        })

    return render(request, 'mistemplates/annual_audit_plan.html', {
        "audit_data": audit_data,
    })


# === CONDUCT INTERNAL AUDITS ===

def conduct_internal_audits(request):
    plans = AnnualPlan.objects.select_related(
        "annual_program__process",
        "lider"
    ).prefetch_related("auditors__user", "audited_users__user", "checklists", "checklists__question")

    data = []
    for plan in plans:
        entry = {
            "plan_id": plan.id,
            "process": plan.annual_program.process.name,
            "year": plan.annual_program.program_header.year,
            "lider": plan.lider.get_full_name(),
            "auditors": [a.user.get_full_name() for a in plan.auditors.all()],
            "audited_users": [a.user.get_full_name() for a in plan.audited_users.all()],
            "checklist": [{
                "question": c.question.question_text,
                "compliance": c.compliance,
                "evidence": c.evidence,
            } for c in plan.checklists.all()],
            "report": None,
            "findings": []
        }

        report = AuditReport.objects.filter(audit=plan.annual_program).first()
        if report:
            entry["report"] = {
                "summary": report.summary,
                "strengths": report.strengths
            }

            findings = Findings.objects.filter(report=report).select_related("requirement")
            entry["findings"] = [{
                "requirement": f.requirement.name if f.requirement else "N/A",
                "text": f.finding_text,
                "classification": f.classification,
            } for f in findings]

        data.append(entry)

    return render(request, "mistemplates/conduct_internal_audits.html", {"audit_data": data})

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
