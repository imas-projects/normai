from django.shortcuts import render, get_object_or_404, redirect
from .forms import AuditTeamForm, AuditedForm, AuditedEvaluationQuestionForm, LeadAuditorEvaluationQuestionForm, AuditProgramHeaderForm, AnnualProgramForm
from .forms import AuditPlanHeaderForm, AssociatedElementsForm, FindingsForm, AuditReportForm, UnifiedRequirementForm, ChecklistForm
from .models import AuditProgramHeader, AuditTeam, AuditPlanHeader, Audited, AnnualProgram, AssociatedElements, Checklist, Requirement, LeadAuditorEvaluationQuestion
from .models import AuditedEvaluationQuestion, AuditReport, Findings
from django.contrib.auth.models import User

from collections import defaultdict, OrderedDict
from datetime import datetime, timedelta
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.forms import modelformset_factory

def audits_home(request):
    return render(request, 'mistemplates/audits.html')

def annual_audit_program(request):
    audit_headers = AuditProgramHeader.objects.all()
    audit_teams = AuditTeam.objects.select_related('person', 'role')

    grouped_team = defaultdict(list)
    for team_member in audit_teams:
        grouped_team[team_member.role.name].append(team_member.person.get_full_name())

    today = datetime.today()
    start_month = today.month - 1 if today.month > 1 else 12
    start_year = today.year if today.month > 1 else today.year - 1
    month_range = [(start_year, start_month)]

    for _ in range(11):
        last_year, last_month = month_range[-1]
        next_month = (last_month % 12) + 1
        next_year = last_year + (1 if next_month == 1 else 0)
        month_range.append((next_year, next_month))

    annual_programs = AnnualProgram.objects.filter(
        year__in={year for year, _ in month_range},
        month__in={month for _, month in month_range}
    ).order_by('year', 'month')

    annual_programs_by_year = OrderedDict()
    for year, month in month_range:
        month_name = datetime(year, month, 1).strftime('%B')
        if year not in annual_programs_by_year:
            annual_programs_by_year[year] = OrderedDict()
        annual_programs_by_year[year][month_name] = annual_programs.filter(year=year, month=month)

    if request.method == "POST":
        if "save_header" in request.POST:
            header_form = AuditProgramHeaderForm(request.POST)
            if header_form.is_valid():
                header_form.save()
                return redirect(reverse('audits:annual_audit_program'))
        elif "add_team_member" in request.POST:
            team_form = AuditTeamForm(request.POST)
            if team_form.is_valid():
                team_form.save()
                return redirect(reverse('audits:annual_audit_program'))
    else:
        header_form = AuditProgramHeaderForm()
        team_form = AuditTeamForm()

    context = {
        'audit_headers': audit_headers,
        'header_form': header_form,
        'team_form': team_form,
        'grouped_team': grouped_team,
        'annual_programs_by_year': annual_programs_by_year,
    }
    return render(request, 'mistemplates/annual_audit_program.html', context)


def annual_audit_plan(request):
    audit_headers = AuditProgramHeader.objects.all()
    audit_plans = AuditPlanHeader.objects.all()
    audit_teams = AuditTeam.objects.select_related('person', 'role')

    audited_people = Audited.objects.select_related('audited_user', 'requirement')
    audit_data = []

    for audited in audited_people:
        associated_elements = AssociatedElements.objects.filter(requirement=audited.requirement).first()

        audit_entry = {
            'requirement': audited.requirement,
            'audited_person': audited.audited_user,
            'audit_date': associated_elements.audit_date if associated_elements else None,
            'audit_time': associated_elements.audit_time if associated_elements else None,
            'audit_team_member': associated_elements.audit_team_member if associated_elements else None,
            'audit_location': associated_elements.audit_location if associated_elements else None,
        }
        audit_data.append(audit_entry)

    grouped_team = defaultdict(list)
    for team_member in audit_teams:
        grouped_team[team_member.role.name].append(team_member.person.get_full_name())

    context = {
        'audit_headers': audit_headers,
        'audit_plans': audit_plans,
        'grouped_team': grouped_team,
        'audit_data': audit_data,
    }

    return render(request, 'mistemplates/annual_audit_plan.html', context)


def conduct_internal_audits(request):
    audited_list = Audited.objects.select_related("requirement", "audited_user")
    associated_elements = AssociatedElements.objects.select_related("requirement", "audit_team_member__person")

    audit_data = []
    for audited in audited_list:
        requirement = audited.requirement
        audit_entry = {
            "requirement": requirement.name if requirement else "N/A",
            "requirement_id": requirement.id if requirement else None,
            "audited": f"{audited.audited_user.first_name} {audited.audited_user.last_name}",
            "auditor": "N/A",
            "findings": [],
            "audit_report": None
        }

        associated_element = associated_elements.filter(requirement=requirement).first()
        if associated_element:
            auditor = associated_element.audit_team_member.person
            audit_entry["auditor"] = f"{auditor.first_name} {auditor.last_name}"

        if requirement:
            findings = Findings.objects.filter(requirement=requirement)
            audit_entry["findings"] = [
                {
                    "finding_text": finding.finding_text,
                    "classification": finding.classification
                }
                for finding in findings
            ]

            audit_report = AuditReport.objects.filter(requirement=requirement).first()
            if audit_report:
                audit_entry["audit_report"] = {
                    "summary": audit_report.summary,
                    "strengths": audit_report.strengths
                }

        audit_data.append(audit_entry)

    context = {"audit_data": audit_data}
    return render(request, "mistemplates/conduct_internal_audits.html", context)

def add_audit_team(request):
    if request.method == 'POST':
        form = AuditTeamForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('audits:audits_home')  
    else:
        form = AuditTeamForm()  

    return render(request, 'mistemplates/add_audit_team.html', {'form': form})

def add_audited(request):
    if request.method == 'POST':
        form = AuditedForm(request.POST)
        if form.is_valid():
            audited_instance = form.save(commit=False)
            audited_instance.audited_user = form.cleaned_data['audited_user']
            audited_instance.save()
            return redirect('audits:audits_home')
    else:
        form = AuditedForm()

    return render(request, 'mistemplates/add_audited.html', {'form': form})

def add_checklist_question(request):
    if request.method == 'POST':
        form = ChecklistQuestionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('audits:conduct_audit')  
    else:
        form = ChecklistQuestionForm()  

    return render(request, 'mistemplates/add_checklist_question.html', {'form': form})

def add_audited_evaluation_question(request):
    if request.method == 'POST':
        form = AuditedEvaluationQuestionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('audits:conduct_audit')  
    else:
        form = AuditedEvaluationQuestionForm()  

    return render(request, 'mistemplates/add_audited_evaluation_question.html', {'form': form})

def add_lead_auditor_evaluation_question(request):
    if request.method == 'POST':
        form = LeadAuditorEvaluationQuestionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('audits:conduct_audit')  
    else:
        form = LeadAuditorEvaluationQuestionForm()  

    return render(request, 'mistemplates/add_lead_auditor_evaluation_question.html', {'form': form})

def add_audit_program_header(request):
    if request.method == 'POST':
        form = AuditProgramHeaderForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('audits:annual_program')  
    else:
        form = AuditProgramHeaderForm()  

    return render(request, 'mistemplates/add_audit_program_header.html', {'form': form})

def add_annual_program(request):
    if request.method == 'POST':
        form = AnnualProgramForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('audits:annual_program')  
    else:
        form = AnnualProgramForm()  

    return render(request, 'mistemplates/add_annual_program.html', {'form': form})

def add_audit_plan_header(request):
    if request.method == 'POST':
        form = AuditPlanHeaderForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('audits:annual_plan')  
    else:
        form = AuditPlanHeaderForm()  

    return render(request, 'mistemplates/add_audit_plan_header.html', {'form': form})

def add_associated_elements(request):
    if request.method == 'POST':
        form = AssociatedElementsForm(request.POST)
        if form.is_valid():
            associated_element = form.save(commit=False)
            associated_element.save()
            return redirect('audits:annual_plan')
    else:
        form = AssociatedElementsForm()

    return render(request, 'mistemplates/add_associated_elements.html', {'form': form})

def add_findings(request):
    if request.method == 'POST':
        form = FindingsForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('audits:conduct_audit')  
    else:
        form = FindingsForm()  

    return render(request, 'mistemplates/add_findings.html', {'form': form})

def add_audit_report(request):
    if request.method == 'POST':
        form = AuditReportForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('audits:conduct_audit')  
    else:
        form = AuditReportForm()

    return render(request, 'mistemplates/add_audit_report.html', {'form': form})

def add_requirement(request):
    if request.method == 'POST':
        form = UnifiedRequirementForm(request.POST)
        if form.is_valid():
            requirement = form.save(commit=False)
            requirement.save()
            return redirect('audits:audits_home')
    else:
        form = UnifiedRequirementForm()
    
    return render(request, 'mistemplates/add_requirement.html', {'form': form})

def add_checklist(request):
    if request.method == "POST":
        form = ChecklistForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('audits:conduct_audit') 
        else:
            return JsonResponse({"status": "error", "errors": form.errors}, status=400)
    
    form = ChecklistForm()
    return render(request, "mistemplates/add_checklist.html", {"form": form})

def get_checklist_data(request, requirement_id):
    if request.method == "GET":
        checklists = Checklist.objects.filter(requirement_id=requirement_id).order_by('order')
        data = []

        for checklist in checklists:
            data.append({
                'id': checklist.id,
                'question_text': checklist.question_text,
                'order': checklist.order,
                'objective_evidence': checklist.objective_evidence,
                'compliance': checklist.compliance,
            })
        
        return JsonResponse(data, safe=False)

def get_audited_questions(request, requirement_id):
    questions = AuditedEvaluationQuestion.objects.filter(requirement_id=requirement_id).order_by('order')

    data = [
        {
            "id": q.id,
            "question_text": q.question_text,
            "order": q.order,
            "rating": q.rating,
        }
        for q in questions
    ]
    
    return JsonResponse(data, safe=False)

def get_lead_auditor_questions(request, requirement_id):
    questions = LeadAuditorEvaluationQuestion.objects.filter(requirement_id=requirement_id).order_by('order')
    
    data = [
        {
            "id": q.id,
            "question_text": q.question_text,
            "order": q.order,
            "rating": q.rating,
        }
        for q in questions
    ]
    
    return JsonResponse(data, safe=False)

