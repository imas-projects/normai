from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from collections import defaultdict, OrderedDict
from datetime import datetime
from itertools import zip_longest
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt
import traceback

from .forms import (
    AuditProgramHeaderForm, AnnualProgramForm, AnnualPlanForm, AnnualProgramUserForm,
    AnnualPlanAuditorForm, AnnualPlanAuditedForm, ChecklistForm, FindingsForm, AuditReportForm,
    ProcessRequirementForm, AuditedEvaluationQuestionForm, AuditorEvaluationForm, LeadAuditorEvaluationQuestionForm
)
from company.models import Requirement

from .models import (
    AuditProgramHeader,ProcessRequirement, AnnualProgram, AnnualProgramUser, 
    AnnualPlan,
    Checklist,
    AuditReport,
    Findings,
    AuditedEvaluationQuestion,
    LeadAuditorEvaluationQuestion
)

from ai_functions.monitoring_functions import suggest_audit_fields, suggest_annual_processes_ai, suggest_audit_users_ai, suggest_leader_ai, suggest_auditor_ai, suggest_audited_ai, suggest_audit_questions, suggest_compliance_rating

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
        auditors = [auditor.user.get_full_name() for auditor in plan.auditors.all()]
        audited_users = [audited.user.get_full_name() for audited in plan.audited_users.all()]

        paired_list = list(zip_longest(auditors, audited_users, fillvalue=None))

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
            "auditors": auditors,
            "audited_users": audited_users,
            "paired_team": paired_list,
        })

    return render(request, 'mistemplates/annual_audit_plan.html', {
        "audit_data": audit_data,
    })


# === CONDUCT INTERNAL AUDITS ===

def conduct_internal_audits(request):
    plans = AnnualPlan.objects.select_related(
        "annual_program__process", "lider"
    ).prefetch_related(
        "auditors__user",
        "audited_users__user",
        "checklists__question",
        "auditor_evaluations__question"
    )

    data = []

    for plan in plans:
        checklist_items = plan.checklists.select_related("question").all()

        checklist = [{
            "orden": item.orden,
            "question": item.question.question_text,
            "requirement": item.question.requirement.name if item.question.requirement else "N/A",
            "compliance": item.compliance,
            "evidence": item.evidence,
        } for item in checklist_items]

        auditor_evals = plan.auditor_evaluations.select_related("question").all()
        auditor_evaluation = [{
            "orden": eval.orden,
            "question": eval.question.question_text,
            "rate": eval.rate
        } for eval in auditor_evals]

        report = AuditReport.objects.filter(audit=plan.annual_program).first()
        report_data = None
        findings_data = []

        if report:
            report_data = {
                "summary": report.summary,
                "strengths": report.strengths
            }

            findings = Findings.objects.filter(report=report).select_related("requirement")
            findings_data = [{
                "requirement": f.requirement.name if f.requirement else "N/A",
                "text": f.finding_text,
                "classification": f.classification,
            } for f in findings]

        lead_eval_queryset = LeadAuditorEvaluationQuestion.objects.filter(type='AUDITOR_LIDER')

        lead_auditor_evaluation = [{
            "question": eval.question_text,
        } for eval in lead_eval_queryset]

        entry = {
            "plan_id": plan.id,
            "process": plan.annual_program.process.name,
            "year": plan.annual_program.program_header.year,
            "leader": plan.lider.get_full_name(),
            "auditors": [aud.user.get_full_name() for aud in plan.auditors.all()],
            "audited_users": [au.user.get_full_name() for au in plan.audited_users.all()],
            "checklist": checklist,
            "auditor_evaluation": auditor_evaluation,
            "lead_auditor_evaluation": lead_auditor_evaluation,
            "report": report_data,
            "findings": findings_data,
        }

        data.append(entry)

    return render(request, "mistemplates/conduct_internal_audits.html", {"audit_data": data})


# === ADD VIEWS ===

def _add_form_view(request, form_class, redirect_url, template_name, use_cleaned_user=False):
    if request.method == "POST":
        form = form_class(request.POST)
        if form.is_valid():
            form.save()
            return redirect(redirect_url)
        else:
            return render(request, template_name, {"form": form})
    else:
        form = form_class()
    return render(request, template_name, {"form": form})

# Vistas add actualizadas y limpias, con formularios correctos y URLs adecuadas

def add_audit_program_header(request):
    return _add_form_view(request, AuditProgramHeaderForm, 'audits:annual_audit_program', 'mistemplates/add_audit_program_header.html')

@require_GET
@csrf_exempt 
def suggest_audit_program_fields(request):
    try:
        year = int(request.GET.get("year", 0))
        if year <= 0:
            return JsonResponse({"error": "Año inválido."}, status=400)

        suggestions = suggest_audit_fields(year)
        return JsonResponse({"suggestions": suggestions})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def add_annual_program(request):
    return _add_form_view(request, AnnualProgramForm, 'audits:annual_audit_program', 'mistemplates/add_annual_program.html')

def suggest_annual_program_processes_view(request):
    program_header_id = request.GET.get('program_header_id')
    if not program_header_id:
        return HttpResponseBadRequest("Falta el parámetro 'program_header_id'")

    try:
        suggestions = suggest_annual_processes_ai(int(program_header_id))
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"suggestions": suggestions})

def add_annual_program_user(request):
    return _add_form_view(request, AnnualProgramUserForm, 'audits:annual_audit_program', 'mistemplates/add_annual_program_user.html')

def suggest_audit_users_view(request):
    annual_program_id = request.GET.get("annual_program_id")

    if not annual_program_id:
        return HttpResponseBadRequest("Falta el parámetro 'annual_program_id'")

    try:
        annual_program = get_object_or_404(AnnualProgram, pk=annual_program_id)
        program_header_id = annual_program.program_header_id
        process_id = annual_program.process_id

        suggestions = suggest_audit_users_ai(
            program_header_id=int(program_header_id),
            process_id=int(process_id),
            max_results=5
        )
    except Exception as e:
        print("Error en suggest_audit_users_view:", e)
        traceback.print_exc()  
        return JsonResponse({"error": f"Error al generar sugerencias: {str(e)}"}, status=500)

    return JsonResponse({"suggestions": suggestions})

def add_annual_plan(request):
    return _add_form_view(request, AnnualPlanForm, 'audits:annual_audit_plan', 'mistemplates/add_annual_plan.html')

def suggest_leader_view(request):
    annual_program_id = request.GET.get("annual_program_id")

    if not annual_program_id:
        return HttpResponseBadRequest("Falta el parámetro 'annual_program_id'")

    try:
        annual_program = get_object_or_404(AnnualProgram, pk=annual_program_id)
        
        suggestions = suggest_leader_ai(
            program_id=annual_program.id,
            max_results=5
        )
    except Exception as e:
        print("Error en suggest_leader_view:", e)
        traceback.print_exc()
        return JsonResponse({"error": f"Error al generar sugerencias: {str(e)}"}, status=500)

    return JsonResponse({"suggestions": suggestions})

    
def add_annual_plan_auditor(request):
    return _add_form_view(request, AnnualPlanAuditorForm, 'audits:annual_audit_plan', 'mistemplates/add_annual_plan_auditor.html')

def suggest_auditor_view(request):
    annual_plan_id = request.GET.get("annual_plan_id")

    if not annual_plan_id:
        return HttpResponseBadRequest("Falta el parámetro 'annual_plan_id'")

    try:
        annual_plan = get_object_or_404(AnnualPlan, pk=annual_plan_id)

        suggestions = suggest_auditor_ai(
            program_id=annual_plan.annual_program.id, 
            max_results=5
        )
    except Exception as e:
        print("Error en suggest_auditor_view:", e)
        traceback.print_exc()
        return JsonResponse({"error": f"Error al generar sugerencias: {str(e)}"}, status=500)

    return JsonResponse({"suggestions": suggestions})


def add_annual_plan_audited(request):
    return _add_form_view(request, AnnualPlanAuditedForm, 'audits:annual_audit_plan', 'mistemplates/add_annual_plan_audited.html')

def suggest_audited_view(request):
    annual_plan_id = request.GET.get("annual_plan_id")

    if not annual_plan_id:
        return HttpResponseBadRequest("Falta el parámetro 'annual_plan_id'")

    try:
        annual_plan = get_object_or_404(AnnualPlan, pk=annual_plan_id)

        suggestions = suggest_audited_ai(
            plan_id=annual_plan.id,  
            max_results=5
        )
    except Exception as e:
        print("Error en suggest_audited_view:", e)
        traceback.print_exc()
        return JsonResponse({"error": f"Error al generar sugerencias: {str(e)}"}, status=500)

    return JsonResponse({"suggestions": suggestions})


def add_checklist(request):
    if request.method == "POST":
        form = ChecklistForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('audits:conduct_internal_audits')
        else:
            return JsonResponse({"status": "error", "errors": form.errors}, status=400)
    return render(request, "mistemplates/add_checklist.html", {"form": ChecklistForm()})

def add_findings(request):
    return _add_form_view(request, FindingsForm, 'audits:conduct_internal_audits', 'mistemplates/add_findings.html')

def add_audit_report(request):
    return _add_form_view(request, AuditReportForm, 'audits:conduct_internal_audits', 'mistemplates/add_audit_report.html')

def add_process_requirement(request):
    return _add_form_view(request, ProcessRequirementForm, 'audits:annual_audit_program', 'mistemplates/add_process_requirement.html')

def add_audited_evaluation_question(request):
    return _add_form_view(request, AuditedEvaluationQuestionForm, 'audits:conduct_internal_audits', 'mistemplates/add_audited_evaluation_question.html')

def suggest_audit_questions_view(request):
    requirement_id = request.GET.get('requirement_id')

    if not requirement_id:
        return HttpResponseBadRequest("Falta el parámetro 'requirement_id'.")

    try:
        requirement = Requirement.objects.get(pk=requirement_id)
    except Requirement.DoesNotExist:
        return HttpResponseBadRequest("El requisito especificado no existe.")

    # Buscar proceso asociado en ProcessRequirement
    # Si hay más de uno, puedes elegir el primero o devolver error o manejar lista
    process_requirement = ProcessRequirement.objects.filter(requirement=requirement).first()

    if not process_requirement:
        return HttpResponseBadRequest("No se encontró proceso asociado al requisito.")

    process_name = process_requirement.process.name

    try:
        questions = suggest_audit_questions(requirement, process_name)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"questions": questions})

@require_POST
@csrf_exempt  
def save_selected_audit_question(request):
    try:
        requirement_id = request.POST.get("requirement_id")
        question_text = request.POST.get("question_text")

        if not requirement_id or not question_text:
            return JsonResponse({"error": "Faltan datos"}, status=400)

        requirement = Requirement.objects.get(pk=requirement_id)

        question = AuditedEvaluationQuestion.objects.create(
            requirement=requirement,
            question_text=question_text,
        )

        return JsonResponse({"success": True, "id": question.id})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def add_auditor_evaluation(request):
    return _add_form_view(request, AuditorEvaluationForm, 'audits:conduct_internal_audits', 'mistemplates/add_auditor_evaluation.html')

def suggest_compliance_rate_view(request):
    audit_id = request.GET.get("audit_id")
    question_id = request.GET.get("question_id")

    if not audit_id or not question_id:
        return HttpResponseBadRequest("Faltan parámetros: audit_id y question_id son obligatorios.")

    try:
        checklist = Checklist.objects.get(
            audit_plan__id=audit_id,
            question__id=question_id
        )
    except Checklist.DoesNotExist:
        tb = traceback.format_exc()
        return JsonResponse({"error": "No se encontró un Checklist con ese audit_id y question_id.", "traceback": tb}, status=400)
    except Exception:
        tb = traceback.format_exc()
        return JsonResponse({"error": "Error inesperado al buscar el Checklist.", "traceback": tb}, status=500)

    try:
        suggested_rate = suggest_compliance_rating(checklist)
    except Exception:
        tb = traceback.format_exc()
        return JsonResponse({"error": "Error al obtener sugerencia de IA.", "traceback": tb}, status=500)

    if suggested_rate is None:
        return JsonResponse({"error": "La IA no pudo determinar un rate válido."}, status=422)

    return JsonResponse({"rate": suggested_rate})




def add_lead_auditor_evaluation_question(request):
    return _add_form_view(request, LeadAuditorEvaluationQuestionForm, 'audits:conduct_internal_audits', 'mistemplates/add_lead_auditor_evaluation_question.html')

'''
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
'''
