from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from collections import defaultdict, OrderedDict
from datetime import datetime
from itertools import zip_longest
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt
import traceback
from django.views.decorators.csrf import csrf_protect

from .forms import (
    AuditProgramHeaderForm, AnnualProgramForm, AnnualPlanForm,
    AnnualPlanAuditorForm, AnnualPlanAuditedForm, ChecklistForm, FindingsForm, AuditReportForm,
    ProcessRequirementForm, AuditedEvaluationQuestionForm, AuditorEvaluationForm, LeadAuditorEvaluationQuestionForm
)
from company.models import Requirement

from .models import (
    AuditProgramHeader,ProcessRequirement, AnnualProgram,
    AnnualPlan,AnnualPlanAuditor,
    Checklist,
    AuditReport,
    Findings,
    AuditedEvaluationQuestion,
    LeadAuditorEvaluationQuestion
)

from processes.models import Process

from ai_functions.monitoring_functions import suggest_audit_fields, suggest_annual_processes_ai, suggest_auditor_ai, suggest_audit_questions, suggest_compliance_rating, classify_finding_ia, suggest_audit_report_fields

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
                "requirements": requirements_by_process.get(program.process_id, [])
            })

        annual_programs_by_year[y][month_name] = enriched_programs

    return render(request, 'mistemplates/annual_audit_program.html', {
        'audit_headers': audit_headers,
        'annual_programs_by_year': annual_programs_by_year,
        'users': all_users,
    })

# === ANNUAL AUDIT PLAN ===

from itertools import zip_longest

def annual_audit_plan(request):
    plans = AnnualPlan.objects.select_related(
        "annual_program__program_header",
        "annual_program__process",
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
        "annual_program__process"
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

        report = AuditReport.objects.filter(audit=plan).first()
        report_data = None
        findings_data = []

        lead_eval_queryset = LeadAuditorEvaluationQuestion.objects.filter(type='AUDITOR_LIDER')

        lead_auditor_evaluation = [{
            "question": eval.question_text,
        } for eval in lead_eval_queryset]

        entry = {
            "plan_id": plan.id,
            "process": plan.annual_program.process.name,
            "year": plan.annual_program.program_header.year,
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

@require_POST
@csrf_protect  # Usa CSRF con protección real
def save_selected_annual_program_process(request):
    try:
        program_header_id = request.POST.get("program_header_id")
        process_id = request.POST.get("process_id")
        month = request.POST.get("month")
        try:
            month = int(month)
            if not (1 <= month <= 12):
                return JsonResponse({"error": "Mes inválido"}, status=400)
        except:
            return JsonResponse({"error": "Mes inválido"}, status=400)

        if not program_header_id or not process_id:
            return JsonResponse({"error": "Faltan datos"}, status=400)

        program_header = AuditProgramHeader.objects.get(pk=program_header_id)
        process = Process.objects.get(pk=process_id)

        AnnualProgram.objects.create(
            program_header=program_header,
            process=process,
            month=month if month else None
        )

        return JsonResponse({"success": True})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def add_annual_plan(request):
    return _add_form_view(request, AnnualPlanForm, 'audits:annual_audit_plan', 'mistemplates/add_annual_plan.html')
    
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

@require_POST
@csrf_exempt
def save_selected_auditor(request):
    try:
        annual_plan_id = request.POST.get("annual_plan_id")
        user_id = request.POST.get("user_id")

        if not annual_plan_id or not user_id:
            return JsonResponse({"error": "Faltan datos"}, status=400)

        annual_plan = get_object_or_404(AnnualPlan, pk=annual_plan_id)
        user = get_object_or_404(User, pk=user_id)

        obj, created = AnnualPlanAuditor.objects.get_or_create(
            annual_plan=annual_plan,
            user=user
        )
        if not created:
            return JsonResponse({"error": "Este auditor ya está asignado al plan."}, status=400)

        return JsonResponse({"success": True, "message": "Auditor guardado correctamente."})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)



def add_annual_plan_audited(request):
    return _add_form_view(request, AnnualPlanAuditedForm, 'audits:annual_audit_plan', 'mistemplates/add_annual_plan_audited.html')
    

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
    ia_error = None

    if request.method == "POST":
        form = FindingsForm(request.POST)

        if "classify_ia" in request.POST:
            if form.is_valid():
                finding_text = form.cleaned_data["finding_text"]
                requirement = form.cleaned_data.get("requirement")

                try:
                    classification = classify_finding_ia(finding_text, requirement)
                    if classification:
                        form.cleaned_data["classification"] = classification
                        form.fields["classification"].initial = classification
                        form.data = form.data.copy()
                        form.data["classification"] = classification
                        messages.success(request, f"Clasificación sugerida: {classification}")
                    else:
                        ia_error = "La IA no pudo determinar una clasificación."
                except Exception as e:
                    ia_error = f"Error al clasificar con IA: {str(e)}"

            # Mostrar el formulario con el campo classification autoseleccionado
            return render(request, "mistemplates/add_findings.html", {
                "form": form,
                "ia_error": ia_error
            })

        elif "save" in request.POST:
            if form.is_valid():
                form.save()
                messages.success(request, "Hallazgo guardado correctamente.")
                return redirect("audits:conduct_internal_audits")

    else:
        form = FindingsForm()

    return render(request, "mistemplates/add_findings.html", {"form": form})

def classify_finding_view(request):
    finding_text = request.GET.get("finding_text")
    requirement_id = request.GET.get("requirement_id")

    if not finding_text:
        return HttpResponseBadRequest("El texto del hallazgo (finding_text) es obligatorio.")

    requirement = None
    if requirement_id:
        try:
            requirement = Requirement.objects.get(id=requirement_id)
        except Requirement.DoesNotExist:
            tb = traceback.format_exc()
            return JsonResponse({
                "error": f"Requisito con ID {requirement_id} no encontrado.",
                "traceback": tb
            }, status=400)
        except Exception:
            tb = traceback.format_exc()
            return JsonResponse({
                "error": "Error inesperado al obtener el requisito.",
                "traceback": tb
            }, status=500)

    try:
        classification = classify_finding_ia(finding_text, requirement)
    except Exception:
        tb = traceback.format_exc()
        return JsonResponse({"error": "Error al clasificar con IA.", "traceback": tb}, status=500)

    if classification is None:
        return JsonResponse({"error": "La IA no pudo determinar una clasificación válida."}, status=422)

    return JsonResponse({"classification": classification})


def add_audit_report(request):
    return _add_form_view(request, AuditReportForm, 'audits:conduct_internal_audits', 'mistemplates/add_audit_report.html')

def suggest_audit_report_view(request):
    audit_plan_id = request.GET.get("audit_plan_id")

    if not audit_plan_id:
        return HttpResponseBadRequest("Falta el parámetro 'audit_plan_id'")

    try:
        audit_plan = AnnualPlan.objects.get(pk=audit_plan_id)
        suggestion = suggest_audit_report_fields(audit_plan.id)
        return JsonResponse({"suggestions": [suggestion]})

    except AnnualPlan.DoesNotExist:
        print(f"AuditPlan con id {audit_plan_id} no existe.")
        return HttpResponseBadRequest("El plan de auditoría no existe.")

    except Exception as e:
        import traceback
        print("Error en suggest_audit_report_view:", e)
        traceback.print_exc()
        return JsonResponse({"error": f"Error al generar el informe: {str(e)}"}, status=500)


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
