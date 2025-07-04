from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.utils.timezone import now
from django.db.models import OuterRef, Subquery
from django.db.models import Q, Count
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
from django.db.models import Avg, Case, When, FloatField, Count, Q, F
from django.db.models.functions import Coalesce

import locale
from babel.dates import format_date

from .forms import (
    AuditProgramHeaderForm, AnnualProgramForm, AnnualPlanForm,
    AnnualPlanAuditorForm, AnnualPlanAuditedForm, ChecklistForm, FindingsForm, AuditReportForm,
    ProcessRequirementForm, AuditedEvaluationQuestionForm, AuditorEvaluationForm, LeadAuditorEvaluationQuestionForm, CorrectiveActionForm, CorrectiveActionFollowUpForm
)
from company.models import Requirement

from .models import (
    AuditProgramHeader,ProcessRequirement, AnnualProgram,
    AnnualPlan,AnnualPlanAuditor,
    Checklist,
    AuditReport,
    Findings,
    AuditedEvaluationQuestion,
    LeadAuditorEvaluationQuestion, CorrectiveAction, CorrectiveActionFollowUp
)

from processes.models import Process

from ai_functions.monitoring_functions import suggest_audit_fields, suggest_annual_processes_ai, suggest_auditor_ai, suggest_audit_questions, suggest_compliance_rating, classify_finding_ia, suggest_audit_report_fields, suggest_corrective_actions

# === BASIC VIEWS ===
@csrf_protect
@login_required
def audits_home(request):
    return render(request, 'mistemplates/audits.html')


# === ANNUAL AUDIT PROGRAM ===
@csrf_protect
@login_required
def annual_audit_program(request):
    audit_headers = AuditProgramHeader.objects.all()
    today = datetime.today()

    # Mes anterior al actual
    start_month = today.month - 1 if today.month > 1 else 12
    start_year = today.year if today.month > 1 else today.year - 1

    # Construir rango de 12 meses desde el mes anterior
    month_range = [(start_year, start_month)]
    for _ in range(11):
        y, m = month_range[-1]
        next_month = (m % 12) + 1
        next_year = y + (1 if next_month == 1 else 0)
        month_range.append((next_year, next_month))

    current_year = today.year
    all_months_current_year = [(current_year, m) for m in range(1, 13)]
    combined_months = sorted(set(all_months_current_year) | set(month_range))

    years = {y for y, _ in combined_months}
    months = {m for _, m in combined_months}

    annual_programs = AnnualProgram.objects.filter(
        program_header__year__in=years,
        month__in=months
    ).select_related("program_header", "process").order_by('program_header__year', 'month')

    requirements_by_process = defaultdict(list)
    for pr in ProcessRequirement.objects.select_related("process"):
        requirements_by_process[pr.process_id].append(pr.requirement)

    annual_programs_by_year = OrderedDict()
    all_users = User.objects.all()

    for y, m in combined_months:
        month_name = format_date(datetime(y, m, 1), "MMMM", locale='es').capitalize()
        if y not in annual_programs_by_year:
            annual_programs_by_year[y] = OrderedDict()

        filtered = annual_programs.filter(program_header__year=y, month=m)
        enriched_programs = [
            {
                "program": program,
                "requirements": requirements_by_process.get(program.process_id, [])
            }
            for program in filtered
        ]

        annual_programs_by_year[y][month_name] = enriched_programs

    # Gráfico de barras: número de requisitos por mes
    requisitos_mes = defaultdict(int)
    for program in annual_programs:
        requisitos = requirements_by_process.get(program.process_id, [])
        key = (program.program_header.year, program.month)
        requisitos_mes[key] += len(requisitos)

    bar_chart_data = [
        {
            "mes": format_date(datetime(y, m, 1), "MMMM", locale='es').capitalize(),
            "total_requisitos": requisitos_mes.get((y, m), 0)
        }
        for y, m in combined_months
    ]

    return render(request, 'mistemplates/annual_audit_program.html', {
        'audit_headers': audit_headers,
        'annual_programs_by_year': annual_programs_by_year,
        'users': all_users,
        'bar_chart_data': bar_chart_data,
    })






# === ANNUAL AUDIT PLAN ===

from itertools import zip_longest
from babel.dates import format_date
from datetime import datetime as dt
@csrf_protect
@login_required
def annual_audit_plan(request):
    plans = AnnualPlan.objects.select_related(
        "annual_program__program_header",
        "annual_program__process",
    ).prefetch_related(
        "auditors__user",
        "audited_users__user"
    )

    audit_data = []
    timeline_data = []

    # Para el gráfico de barras apiladas
    auditor_counter = defaultdict(int)
    audited_counter = defaultdict(int)

    for plan in plans:
        auditors = [auditor.user.get_full_name() for auditor in plan.auditors.all()]
        audited_users = [audited.user.get_full_name() for audited in plan.audited_users.all()]

        # Contar auditorías por usuario
        for auditor in auditors:
            auditor_counter[auditor] += 1
        for audited in audited_users:
            audited_counter[audited] += 1

        paired_list = list(zip_longest(auditors, audited_users, fillvalue=None))

        open_dt = dt.combine(plan.audit_opening_date, plan.audit_opening_time)
        close_dt = dt.combine(plan.audit_closing_date, plan.audit_closing_time)

        open_ts = int(open_dt.timestamp() * 1000)
        close_ts = int(close_dt.timestamp() * 1000)

        if plan.annual_program and plan.annual_program.program_header and plan.annual_program.month:
            month_name = format_date(
                dt(plan.annual_program.program_header.year, plan.annual_program.month, 1), 
                'MMMM', 
                locale='es'
            ).capitalize()
        else:
            month_name = None

        audit_data.append({
            "plan_id": plan.id,
            "process": plan.annual_program.process.name if plan.annual_program and plan.annual_program.process else None,
            "year": plan.annual_program.program_header.year if plan.annual_program and plan.annual_program.program_header else None,
            "month": month_name,
            "audit_opening_date": plan.audit_opening_date,
            "audit_closing_date": plan.audit_closing_date,
            "audit_opening_time": plan.audit_opening_time,
            "audit_closing_time": plan.audit_closing_time,
            "audit_opening_location": plan.audit_opening_location,
            "audit_closing_location": plan.audit_closing_location,
            "auditors": auditors,
            "audited_users": audited_users,
            "paired_team": paired_list,
        })

        timeline_data.append({
            "x": f"Plan {plan.id} ({plan.annual_program.process.name if plan.annual_program else 'Sin proceso'})",
            "y": [open_ts, close_ts]
        })

    # Combinar todos los usuarios únicos
    all_users = sorted(set(list(auditor_counter.keys()) + list(audited_counter.keys())))
    auditor_data = [auditor_counter.get(user, 0) for user in all_users]
    audited_data = [audited_counter.get(user, 0) for user in all_users]

    return render(request, 'mistemplates/annual_audit_plan.html', {
        "audit_data": audit_data,
        "timeline_data": timeline_data,
        "user_labels": all_users,
        "auditor_data": auditor_data,
        "audited_data": audited_data,
    })




# === CONDUCT INTERNAL AUDITS ===
@csrf_protect
@login_required
def conduct_internal_audits(request):
    classification_map = {
        'NC_MAYOR': 'No Conformidad Mayor',
        'NC_MENOR': 'No Conformidad Menor',
        'OPORTUNIDAD_MEJORA': 'Oportunidad de mejora',
    }

    # Traemos los planes con relaciones necesarias para evitar consultas múltiples
    plans = AnnualPlan.objects.select_related(
        "annual_program__process",
        "annual_program__program_header"
    ).prefetch_related(
        "auditors__user",
        "audited_users__user",
        "checklists__question__requirement",
        "auditor_evaluations__question__requirement",
        "findings",
    )

    data = []

    for plan in plans:
        # Construimos checklist con orden label
        checklist = []
        for item in plan.checklists.all():
            item_dict = item.as_dict()
            item_dict["orden_label"] = f"P{item.orden}"
            checklist.append(item_dict)

        # Evaluaciones del auditor
        auditor_evaluation = [eval.as_dict() for eval in plan.auditor_evaluations.all()]

        # Reporte del plan (solo uno)
        report = AuditReport.objects.filter(audit_plan=plan).first()
        report_data = report.as_dict() if report else None

        # Hallazgos con texto de clasificación
        findings_data = []
        for finding in plan.findings.all():
            f_dict = finding.as_dict()
            f_dict["classification_text"] = classification_map.get(f_dict["classification"], f_dict["classification"])
            findings_data.append(f_dict)

        # Acciones correctivas y sus seguimientos
        corrective_actions = []
        if report:
            for action in report.corrective_actions.select_related("responsible_user").prefetch_related("followups").all():
                action_dict = action.as_dict()
                responsible_user = action.responsible_user
                action_dict["responsible_user"]["full_name"] = responsible_user.get_full_name()
                action_dict["followups"] = [f.as_dict() for f in action.followups.all()]
                corrective_actions.append(action_dict)

        entry = {
            "plan_id": plan.id,
            "process": plan.annual_program.process.name,
            "year": plan.annual_program.program_header.year,
            "auditors": [aud.user.get_full_name() for aud in plan.auditors.all()],
            "audited_users": [au.user.get_full_name() for au in plan.audited_users.all()],
            "checklist": checklist,
            "auditor_evaluation": auditor_evaluation,
            "report": report_data,
            "findings": findings_data,
            "corrective_actions": corrective_actions,
        }
        data.append(entry)

    # --- Datos para los gráficos ---

    # === Distribución de No Conformidades por Clasificación ===
    # Filtramos findings relacionados con auditorías del año actual
    findings_dist = (
        Findings.objects
        #.filter(audit_plan__annual_program__program_header__year=current_year)
        .values('classification')
        .annotate(total=Count('id'))
    )

    # Mapear para mostrar etiquetas legibles y evitar que falte alguna categoría
    clasificaciones_map = {
        'NC_MAYOR': 'No Conformidad Mayor',
        'NC_MENOR': 'No Conformidad Menor',
        'OPORTUNIDAD_MEJORA': 'Oportunidad de mejora',
    }

    # Inicializar con 0 para todas las categorías
    clasificaciones_labels = []
    clasificaciones_values = []


    # 4) Gráfico de dispersión: duración acciones correctivas vs severidad
    severity_map = {'NC_MAYOR': 3, 'NC_MENOR': 2, 'OPORTUNIDAD_MEJORA': 1}
    scatter_data = []

    acciones = CorrectiveAction.objects.select_related('audit_report').filter(
        audit_report__audit_plan__findings__classification__in=['NC_MAYOR', 'NC_MENOR', 'OPORTUNIDAD_MEJORA']
    ).distinct()

    for action in acciones:
        findings = action.audit_report.audit_plan.findings.all()
        if findings.exists():
            sev_num = severity_map.get(findings.first().classification, 0)
            duracion_dias = (now().date() - action.due_date).days if action.due_date else 0

            scatter_data.append({
                'x': duracion_dias,
                'y': sev_num,
                'label': findings.first().classification,
            })

    context = {
        "scatter_data": scatter_data,
        "clasificaciones_labels": clasificaciones_labels,
        "clasificaciones_values": clasificaciones_values,
    }

    return render(request, "mistemplates/conduct_internal_audits.html", context)


# === ADD VIEWS ===
@csrf_protect
@login_required
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
@login_required
def suggest_audit_program_fields(request):
    try:
        year = int(request.GET.get("year", 0))
        if year <= 0:
            return JsonResponse({"error": "Año inválido."}, status=400)

        suggestions = suggest_audit_fields(year)
        return JsonResponse({"suggestions": suggestions})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@login_required
def add_annual_program(request):
    return _add_form_view(request, AnnualProgramForm, 'audits:annual_audit_program', 'mistemplates/add_annual_program.html')

@login_required
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
@login_required
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

@login_required
def add_annual_plan(request):
    return _add_form_view(request, AnnualPlanForm, 'audits:annual_audit_plan', 'mistemplates/add_annual_plan.html')

@login_required    
def add_annual_plan_auditor(request):
    return _add_form_view(request, AnnualPlanAuditorForm, 'audits:annual_audit_plan', 'mistemplates/add_annual_plan_auditor.html')

@login_required
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
@login_required
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


@login_required
def add_annual_plan_audited(request):
    return _add_form_view(request, AnnualPlanAuditedForm, 'audits:annual_audit_plan', 'mistemplates/add_annual_plan_audited.html')
    
@login_required
def add_checklist(request):
    if request.method == "POST":
        form = ChecklistForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('audits:conduct_internal_audits')
        else:
            return JsonResponse({"status": "error", "errors": form.errors}, status=400)
    return render(request, "mistemplates/add_checklist.html", {"form": ChecklistForm()})
    
@login_required
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
                    ia_error += "\n" + traceback.format_exc()
                    print(ia_error)  # También imprimir en consola para debug

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

@login_required
def classify_finding_view(request):
    finding_text = request.GET.get("finding_text")
    requirement_id = request.GET.get("requirement_id")

    if not finding_text:
        return HttpResponseBadRequest("El texto del hallazgo (finding_text) es obligatorio.")

    requirement = None
    if requirement_id:
        try:
            requirement = ProcessRequirement.objects.get(id=requirement_id)
        except ProcessRequirement.DoesNotExist:
            tb = traceback.format_exc()
            print(tb)
            return JsonResponse({
                "error": f"Requisito con ID {requirement_id} no encontrado.",
                "traceback": tb
            }, status=400)
        except Exception:
            tb = traceback.format_exc()
            print(tb)
            return JsonResponse({
                "error": "Error inesperado al obtener el requisito.",
                "traceback": tb
            }, status=500)

    try:
        classification = classify_finding_ia(finding_text, requirement)
    except Exception:
        tb = traceback.format_exc()
        print(tb) 
        return JsonResponse({"error": "Error al clasificar con IA.", "traceback": tb}, status=500)

    if classification is None:
        return JsonResponse({"error": "La IA no pudo determinar una clasificación válida."}, status=422)

    return JsonResponse({"classification": classification})

@login_required
def add_audit_report(request):
    return _add_form_view(request, AuditReportForm, 'audits:conduct_internal_audits', 'mistemplates/add_audit_report.html')

@login_required
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

@login_required
def add_process_requirement(request):
    return _add_form_view(request, ProcessRequirementForm, 'audits:annual_audit_program', 'mistemplates/add_process_requirement.html')

@login_required
def add_audited_evaluation_question(request):
    return _add_form_view(request, AuditedEvaluationQuestionForm, 'audits:conduct_internal_audits', 'mistemplates/add_audited_evaluation_question.html')

@login_required
def suggest_audit_questions_view(request):
    requirement_id = request.GET.get('requirement_id')

    if not requirement_id:
        return HttpResponseBadRequest("Falta el parámetro 'requirement_id'.")

    try:
        process_requirement = ProcessRequirement.objects.select_related("process").get(pk=requirement_id)
    except ProcessRequirement.DoesNotExist:
        return HttpResponseBadRequest("El requisito especificado no existe.")

    process_name = process_requirement.process.name

    try:
        questions = suggest_audit_questions(process_requirement, process_name)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"questions": questions})

@require_POST
@csrf_exempt 
@login_required 
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

@login_required
def add_auditor_evaluation(request):
    return _add_form_view(request, AuditorEvaluationForm, 'audits:conduct_internal_audits', 'mistemplates/add_auditor_evaluation.html')

@login_required
def suggest_compliance_rate_view(request):
    audit_id = request.GET.get("audit_id")
    question_id = request.GET.get("question_id")

    if not audit_id or not question_id:
        return HttpResponseBadRequest("Faltan parámetros")

    try:
        checklist_obj = Checklist.objects.get(audit_plan_id=audit_id, question_id=question_id)
        rating = suggest_compliance_rating(checklist_obj)
        if rating is None:
            return JsonResponse({"error": "Error IA: Error al obtener sugerencia de IA."}, status=500)
        return JsonResponse({"rating": rating})

    except Checklist.DoesNotExist:
        return JsonResponse({"error": "Checklist no encontrado"}, status=404)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"error": f"Error interno: {str(e)}"}, status=500)


@login_required
def add_lead_auditor_evaluation_question(request):
    return _add_form_view(request, LeadAuditorEvaluationQuestionForm, 'audits:conduct_internal_audits', 'mistemplates/add_lead_auditor_evaluation_question.html')

@login_required
def add_corrective_action(request):
    return _add_form_view(
        request,
        CorrectiveActionForm,
        'audits:conduct_internal_audits',
        'mistemplates/add_corrective_action.html'
    )

@login_required
def suggest_corrective_action_view(request):
    audit_report_id = request.GET.get("audit_report_id")

    if not audit_report_id:
        return HttpResponseBadRequest("Falta el parámetro 'audit_report_id'")

    try:
        audit_report = get_object_or_404(AuditReport, pk=audit_report_id)
        suggestions = suggest_corrective_actions(audit_report.id)
        return JsonResponse({"suggestions": suggestions})

    except Exception as e:
        import traceback
        print("Error en suggest_corrective_action_view:", e)
        traceback.print_exc()
        return JsonResponse({"error": f"Error al generar las acciones correctivas: {str(e)}"}, status=500)

@login_required
def add_corrective_action_followup(request):
    return _add_form_view(
        request,
        CorrectiveActionFollowUpForm,
        'audits:conduct_internal_audits',  
        'mistemplates/add_corrective_action_followup.html'
    )


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
