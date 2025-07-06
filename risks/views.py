from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import RiskIdentification, RiskEvaluation, RiskTreatment, ContingencyPlan, Reevaluation
from .forms import RiskIdentificationForm, RiskEvaluationForm, RiskTreatmentForm, ContingencyPlanForm, ReevaluationForm
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from collections import defaultdict
from django.http import FileResponse
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO
from datetime import date
from django.template.loader import render_to_string
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.csrf import csrf_protect
from company.models import Area
import json
from processes.models import Process
from collections import Counter
from django.db.models import Count, Q, F, Value
from django.db.models.functions import TruncMonth
from django.utils.timezone import now
import datetime


from ai_functions.monitoring_functions import suggest_risk_fields, suggest_controls, suggest_rating_ranges, suggest_risk_level, suggest_treatment_action, suggest_contingency_actions, suggest_reevaluation_rating_ranges, suggest_reevaluation_risk_level

@login_required
def create_risk(request):
    all_risks = RiskIdentification.objects.select_related('area', 'process').all()

    # Agrupar por Área y Proceso
    grouped_risks = {}
    for risk in all_risks:
        key = (risk.area, risk.process)
        if key not in grouped_risks:
            grouped_risks[key] = []
        grouped_risks[key].append(risk)

    evaluations = RiskEvaluation.objects.select_related('risk').all()
    contingency_plans = ContingencyPlan.objects.select_related('risk').all()
    tratamientos = RiskTreatment.objects.select_related('risk').all()
    reevaluations_qs = Reevaluation.objects.select_related('risk').all()

    # === A. Riesgos por Nivel y Proceso ===
    riesgos_eval = (
        RiskEvaluation.objects
        .values(nombre_proceso=F('risk__process__name'))
        .annotate(
            alto=Count('id', filter=Q(risk_level='High')),
            moderado=Count('id', filter=Q(risk_level='Moderate')),
            bajo=Count('id', filter=Q(risk_level='Low'))
        )
        .order_by('nombre_proceso')
    )

    riesgos_reeval = (
        Reevaluation.objects
        .values(nombre_proceso=F('risk__process__name'))
        .annotate(
            alto=Count('id', filter=Q(risk_level='High')),
            moderado=Count('id', filter=Q(risk_level='Moderate')),
            bajo=Count('id', filter=Q(risk_level='Low'))
        )
        .order_by('nombre_proceso')
    )

    def descomponer(queryset):
        procesos, altos, moderados, bajos = [], [], [], []
        for r in queryset:
            procesos.append(r['nombre_proceso'])
            altos.append(r['alto'])
            moderados.append(r['moderado'])
            bajos.append(r['bajo'])
        return procesos, altos, moderados, bajos

    procesos_eval, altos_eval, moderados_eval, bajos_eval = descomponer(riesgos_eval)
    procesos_reeval, altos_reeval, moderados_reeval, bajos_reeval = descomponer(riesgos_reeval)

    # === A. Pie Chart Riesgo por Nivel ===
    pie_eval = RiskEvaluation.objects.values('risk_level').annotate(total=Count('id'))
    pie_reeval = Reevaluation.objects.values('risk_level').annotate(total=Count('id'))

    pie_eval_labels = [nivel['risk_level'] for nivel in pie_eval]
    pie_eval_values = [nivel['total'] for nivel in pie_eval]
    pie_reeval_labels = [nivel['risk_level'] for nivel in pie_reeval]
    pie_reeval_values = [nivel['total'] for nivel in pie_reeval]

    # === A. Pie Chart Acciones de Contingencia por Tipo ===
    contingency_actions = ContingencyPlan.objects.values_list('contingency_actions', flat=True)
    flat_actions = [accion for acciones in contingency_actions for accion in acciones]
    action_counter = Counter(flat_actions)
    acciones_labels = list(action_counter.keys())
    acciones_values = list(action_counter.values())

    # === B. FODA-Riesgo (Bubble Chart) ===
    foda_eval = list(
        RiskEvaluation.objects.values('severity', 'occurrence', 'detection', 'risk_level')
    )
    foda_reeval = list(
        Reevaluation.objects.values('severity', 'occurrence', 'detection', 'risk_level')
    )

    return render(request, 'mistemplates/risks.html', {
        'grouped_risks': grouped_risks,
        'evaluations': evaluations,
        'treatments': tratamientos,
        'contingency_plans': contingency_plans,
        'reevaluations': reevaluations_qs,

        # A - Evaluation
        'procesos_eval': procesos_eval,
        'riesgo_alto_eval': altos_eval,
        'riesgo_moderado_eval': moderados_eval,
        'riesgo_bajo_eval': bajos_eval,
        'pie_labels_eval': pie_eval_labels,
        'pie_values_eval': pie_eval_values,

        # A - Reevaluation
        'procesos_reeval': procesos_reeval,
        'riesgo_alto_reeval': altos_reeval,
        'riesgo_moderado_reeval': moderados_reeval,
        'riesgo_bajo_reeval': bajos_reeval,
        'pie_labels_reeval': pie_reeval_labels,
        'pie_values_reeval': pie_reeval_values,

        # A - Acciones
        'acciones_labels': acciones_labels,
        'acciones_values': acciones_values,

        # B - FODA
        'foda_data_eval': foda_eval,
        'foda_data_reeval': foda_reeval,
    })







@login_required
def add_risk_identification(request):
    if request.method == 'POST':
        form = RiskIdentificationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('risks:risks')
    else:
        form = RiskIdentificationForm()

    return render(request, 'mistemplates/add_risk_identification.html', {
        'form': form
    })

@require_POST
@csrf_exempt
@login_required  
def save_selected_risk_identification(request):
    try:
        area_id = request.POST.get("area_id")
        process_id = request.POST.get("process_id")
        identified_risk = request.POST.get("identified_risk")
        consequences = request.POST.get("consequences")
        source = request.POST.get("source")  

        if not all([area_id, process_id, identified_risk, consequences, source]):
            return JsonResponse({"error": "Faltan datos"}, status=400)

        area = Area.objects.get(pk=area_id)
        process = Process.objects.get(pk=process_id)

        risk = RiskIdentification.objects.create(
            area=area,
            process=process,
            identified_risk=identified_risk,
            consequences=consequences,
            source=source
        )

        return JsonResponse({"success": True, "id": risk.id})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@login_required
def get_suggestions(request):
    area_id = request.GET.get('area')
    process_id = request.GET.get('process')

    if not area_id or not process_id:
        return JsonResponse({'error': 'Faltan parámetros'}, status=400)

    try:
        area_obj = Area.objects.get(id=area_id)
        process_obj = Process.objects.get(id=process_id)
    except (Area.DoesNotExist, Process.DoesNotExist):
        return JsonResponse({'error': 'Área o proceso no encontrado'}, status=404)

    suggestions = suggest_risk_fields(area_obj.name, process_obj.name)

    if not suggestions or not isinstance(suggestions, list):
        return JsonResponse({'error': 'No se encontraron sugerencias'}, status=404)

    return JsonResponse(suggestions, safe=False)

@login_required
def add_risk_evaluation(request):
    suggestion_data = None
    risk_id = request.GET.get("risk_id")

    if request.method == 'POST':
        form = RiskEvaluationForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True, 'message': 'Risk evaluation saved successfully'}, status=200)
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    else:
        form = RiskEvaluationForm()
        if risk_id:
            try:
                suggestion_data = suggest_evaluation_fields(risk_id=int(risk_id))
            except Exception as e:
                suggestion_data = {"error": f"Error al generar sugerencias: {str(e)}"}

    return render(
        request,
        'mistemplates/add_risk_evaluation.html',
        {
            'form': form,
            'suggestion_data': suggestion_data,
        }
    )




@login_required
def get_controls_suggestions(request):
    risk_id = request.GET.get('risk_id')

    if not risk_id:
        return JsonResponse({'error': 'Falta el parámetro obligatorio risk_id'}, status=400)

    try:
        suggestions = suggest_controls(int(risk_id))

        if "error" in suggestions:
            print(f"Error en suggest_controls: {suggestions['error']}")  # <-- DEBUG
            return JsonResponse({'error': suggestions["error"]}, status=400)

        return JsonResponse(suggestions)

    except Exception as e:
        print(f"Excepción en get_controls_suggestions: {e}")  # <-- DEBUG
        return JsonResponse({'error': f'Error al generar sugerencias de controles: {str(e)}'}, status=500)

@csrf_exempt
@login_required
def get_ranges_suggestions(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    risk_id = data.get('risk_id')
    preventive = data.get("preventive_controls", "")
    detection = data.get("detection_controls", "")

    if not risk_id or not preventive or not detection:
        return JsonResponse({'error': 'Faltan parámetros'}, status=400)

    preventive_list = preventive.split("\n")
    detection_list = detection.split("\n")

    try:
        suggestions = suggest_rating_ranges(int(risk_id), preventive_list, detection_list)

        if "error" in suggestions:
            return JsonResponse({'error': suggestions["error"]}, status=400)

        return JsonResponse(suggestions)

    except Exception as e:
        return JsonResponse({'error': f'Error al generar sugerencias de rangos: {str(e)}'}, status=500)

@login_required
def get_level_suggestions(request):
    risk_id = request.GET.get('risk_id')

    if not risk_id:
        return JsonResponse({'error': 'Falta el parámetro obligatorio risk_id'}, status=400)

    preventive = request.GET.get("preventive_controls", "")
    detection = request.GET.get("detection_controls", "")
    preventive_list = preventive.split("\n")
    detection_list = detection.split("\n")

    severity = request.GET.get("severity")
    occurrence = request.GET.get("occurrence")
    detection_score = request.GET.get("detection")

    if not all([severity, occurrence, detection_score]):
        return JsonResponse({'error': 'Faltan datos para calcular el nivel de riesgo'}, status=400)

    try:
        suggestions = suggest_risk_level(
            int(risk_id),
            preventive_list,
            detection_list,
            int(severity),
            int(occurrence),
            int(detection_score)
        )

        if "error" in suggestions:
            return JsonResponse({'error': suggestions["error"]}, status=400)

        return JsonResponse(suggestions)

    except Exception as e:
        return JsonResponse({'error': f'Error al generar sugerencias de nivel de riesgo: {str(e)}'}, status=500)

@login_required
def add_risk_treatment(request):
    if request.method == 'POST':
        form = RiskTreatmentForm(request.POST)

        if form.is_valid():
            form.save()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Tratamiento de riesgo guardado correctamente'}, status=200)
            else:
                return redirect('risks:add_risk_treatment') 

        else:
            print("ERRORES DEL FORMULARIO:", form.errors)
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'error': form.errors}, status=400)
            else:
                return render(request, 'mistemplates/add_risk_treatment.html', {'form': form})

    else:
        form = RiskTreatmentForm()

    return render(request, 'mistemplates/add_risk_treatment.html', {'form': form})

@login_required
def get_treatment_suggestions(request):
    """
    Endpoint para obtener sugerencias de acciones correctivas de tratamiento para un riesgo específico.
    Parámetro esperado: risk_id (en GET)
    """

    risk_id = request.GET.get('risk_id')
    max_results = request.GET.get('max_results', 1)

    if not risk_id:
        return JsonResponse({'error': 'Falta parámetro risk_id'}, status=400)

    try:
        max_results = int(max_results)
        if max_results < 1:
            max_results = 1
    except ValueError:
        max_results = 1

    suggestions = suggest_treatment_action(risk_id, max_results=max_results)

    if not suggestions or not isinstance(suggestions, list):
        return JsonResponse({'error': 'No se encontraron sugerencias'}, status=404)

    return JsonResponse(suggestions, safe=False)

@login_required
def add_contingency_plan(request):
    if request.method == 'POST':
        form = ContingencyPlanForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True, 'message': 'Contingency plan saved successfully'}, status=200)  
        else:
            return JsonResponse({'error': form.errors}, status=400)
    else:
        form = ContingencyPlanForm()

    return render(request, 'mistemplates/add_contingency_plan.html', {'form': form})

def get_contingency_suggestions(request):
    """
    Endpoint que devuelve sugerencias de acciones de contingencia para un riesgo específico.
    Parámetros esperados (GET):
    - risk_id (obligatorio)
    - max_results (opcional, por defecto 3)
    """
    risk_id = request.GET.get('risk_id')
    max_results = request.GET.get('max_results', 3)

    if not risk_id:
        return JsonResponse({'error': 'Parámetro "risk_id" es requerido.'}, status=400)

    try:
        max_results = int(max_results)
        if max_results < 1:
            max_results = 3
    except ValueError:
        max_results = 3

    suggestions = suggest_contingency_actions(risk_id=risk_id, max_results=max_results)

    if not suggestions:
        return JsonResponse({'error': 'No se pudieron generar sugerencias.'}, status=404)

    return JsonResponse(suggestions, safe=False)

@login_required
def add_reevaluation(request):
    suggestion_data = None
    risk_id = request.GET.get("risk_id")

    if request.method == 'POST':
        form = ReevaluationForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True, 'message': 'Reevaluación guardada correctamente'}, status=200)
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    else:
        form = ReevaluationForm()
        if risk_id:
            try:
                suggestion_data = suggest_reevaluation_rating_ranges(risk_id=int(risk_id))
            except Exception as e:
                suggestion_data = {"error": f"Error al generar sugerencias: {str(e)}"}

    return render(
        request,
        'mistemplates/add_reevaluation.html',
        {
            'form': form,
            'suggestion_data': suggestion_data,
            'risk_id': risk_id 
        }
    )

@csrf_exempt
@login_required
def get_reevaluation_ranges_suggestions(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    risk_id = data.get('risk_id')

    if not risk_id:
        return JsonResponse({'error': 'Falta el parámetro risk_id'}, status=400)

    try:
        suggestions = suggest_reevaluation_rating_ranges(int(risk_id))

        if "error" in suggestions:
            return JsonResponse({'error': suggestions["error"]}, status=400)

        return JsonResponse(suggestions)

    except Exception as e:
        return JsonResponse({'error': f'Error al generar sugerencias de rangos: {str(e)}'}, status=500)
        
@login_required
def get_reevaluation_level_suggestions(request):
    risk_id = request.GET.get('risk_id')

    if not risk_id:
        return JsonResponse({'error': 'Falta el parámetro obligatorio risk_id'}, status=400)

    severity = request.GET.get("severity")
    occurrence = request.GET.get("occurrence")
    detection_score = request.GET.get("detection")

    if not all([severity, occurrence, detection_score]):
        return JsonResponse({'error': 'Faltan datos para calcular el nivel de riesgo'}, status=400)

    try:
        suggestions = suggest_reevaluation_risk_level(
            int(risk_id),
            int(severity),
            int(occurrence),
            int(detection_score)
        )

        if "error" in suggestions:
            return JsonResponse({'error': suggestions["error"]}, status=400)

        return JsonResponse(suggestions)

    except Exception as e:
        return JsonResponse({'error': f'Error al generar sugerencias de nivel de riesgo: {str(e)}'}, status=500)


@login_required
def edit_risk_identification(request, risk_id):
    risk = get_object_or_404(RiskIdentification, id=risk_id)
    
    if request.method == 'POST':
        form = RiskIdentificationForm(request.POST, instance=risk)
        if form.is_valid():
            form.save()
            return redirect('risks:risks')
    else:
        form = RiskIdentificationForm(instance=risk)

    return render(request, 'mistemplates/edit_risk_identification.html', {'form': form, 'risk': risk})

@login_required
def edit_risk_evaluation(request, risk_id):
    evaluation = get_object_or_404(RiskEvaluation, id=risk_id)

    if request.method == 'POST':
        form = RiskEvaluationForm(request.POST, instance=evaluation)
        if form.is_valid():
            form.save()
            return redirect('risks:risks')
        else:
            return JsonResponse({'error': form.errors}, status=400)
    else:
        form = RiskEvaluationForm(instance=evaluation)

    return render(request, 'mistemplates/edit_risk_evaluation.html', {'form': form, 'evaluation': evaluation})

@login_required
def edit_risk_treatment(request, risk_id):
    treatment = get_object_or_404(RiskTreatment, id=risk_id)

    if request.method == 'POST':
        form = RiskTreatmentForm(request.POST, instance=treatment)
        if form.is_valid():
            form.save()
            return redirect('risks:risks')
        else:
            return JsonResponse({'error': form.errors}, status=400)
    else:
        form = RiskTreatmentForm(instance=treatment)

    return render(request, 'mistemplates/edit_risk_treatment.html', {'form': form, 'treatment': treatment})

@login_required
def edit_contingency_plan(request, risk_id):
    plan = get_object_or_404(ContingencyPlan, id=risk_id)

    if request.method == 'POST':
        form = ContingencyPlanForm(request.POST, instance=plan)
        if form.is_valid():
            form.save()
            return redirect('risks:risks')
        else:
            return JsonResponse({'error': form.errors}, status=400)
    else:
        form = ContingencyPlanForm(instance=plan)

    return render(request, 'mistemplates/edit_contingency_plan.html', {'form': form, 'plan': plan})

@login_required
def edit_reevaluation(request, risk_id):
    reevaluation = get_object_or_404(Reevaluation, id=risk_id)

    if request.method == 'POST':
        form = ReevaluationForm(request.POST, instance=reevaluation)
        if form.is_valid():
            form.save()
            return redirect('risks:risks')
    else:
        form = ReevaluationForm(instance=reevaluation)

    return render(request, 'mistemplates/edit_reevaluation.html', {'form': form, 'reevaluation': reevaluation})

from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, ListFlowable, ListItem, PageBreak
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.pdfgen.canvas import Canvas
from io import BytesIO
from datetime import date
from django.http import FileResponse
from django.shortcuts import get_object_or_404


def generate_risks_pdf(request, area_name): 
    area = get_object_or_404(Area, name=area_name)  
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()

    # Estilos personalizados
    title_style = ParagraphStyle(
        name='Title', 
        fontName='Helvetica-Bold', 
        fontSize=22, 
        alignment=TA_CENTER, 
        spaceAfter=20, 
        leading=28,  # aumento interlineado para que no colapse
        textColor=colors.HexColor("#003366")
    )
    heading_style = ParagraphStyle(
        name='Heading', 
        fontName='Helvetica-Bold', 
        fontSize=14, 
        textColor=colors.HexColor("#003366"), 
        spaceBefore=15, 
        spaceAfter=10
    )
    subheading_style = ParagraphStyle(
        name='SubHeading', 
        fontName='Helvetica-Bold', 
        fontSize=12, 
        textColor=colors.HexColor("#004C99"), 
        spaceBefore=10, 
        spaceAfter=6
    )
    normal_style = styles["BodyText"]
    normal_style.spaceAfter = 6
    normal_style.leading = 14  # interlineado suficiente

    risk_title_style = ParagraphStyle(
        name='RiskTitle', 
        fontName='Helvetica-Bold', 
        fontSize=14, 
        textColor=colors.HexColor("#990000"), 
        spaceAfter=8,
        leading=18  # interlineado para que título no colapse
    )

    # Encabezado general
    elements.append(Paragraph(f"Reporte de Identificación y Gestión de Riesgos - Área: {area.name}", title_style))
    elements.append(Paragraph(f"Fecha de generación: {date.today().strftime('%d/%m/%Y')}", normal_style))
    elements.append(Spacer(1, 12))

    risks = RiskIdentification.objects.filter(area=area)

    if not risks.exists():
        elements.append(Paragraph("No se encontraron riesgos asociados a esta área.", normal_style))
    else:
        for idx, risk in enumerate(risks, start=1):
            risk_header = f"Riesgo #{idx}: {risk.identified_risk}"
            elements.append(Paragraph(risk_header, risk_title_style))
            elements.append(Paragraph(f"<b>Proceso:</b> {risk.process.name}", normal_style))
            elements.append(Paragraph(f"<b>Consecuencias:</b>", subheading_style))
            elements.append(Paragraph(risk.consequences, normal_style))
            if risk.source:
                elements.append(Paragraph(f"<b>Fuente:</b> {risk.source}", normal_style))

            # Evaluaciones
            evaluations = RiskEvaluation.objects.filter(risk=risk)
            if evaluations.exists():
                elements.append(Paragraph("Evaluaciones de Riesgo", heading_style))

                data = [["Severidad", "Controles Preventivos", "Ocurrencia", "Controles de Detección", "Detección", "Nivel de Riesgo"]]
                for ev in evaluations:
                    risk_level_color = {
                        'High': colors.HexColor("#d9534f"),  # rojo
                        'Moderate': colors.HexColor("#f0ad4e"),  # naranja
                        'Low': colors.HexColor("#5cb85c")  # verde
                    }.get(ev.risk_level, colors.black)

                    # Usar Paragraph para textos largos, para que hagan wrap
                    preventive_controls = Paragraph(ev.current_preventive_controls or "-", normal_style)
                    detection_controls = Paragraph(ev.current_detection_controls or "-", normal_style)
                    risk_level_paragraph = Paragraph(f'<font color="{risk_level_color}"><b>{ev.risk_level}</b></font>', normal_style)

                    data.append([
                        str(ev.severity),
                        preventive_controls,
                        str(ev.occurrence),
                        detection_controls,
                        str(ev.detection),
                        risk_level_paragraph
                    ])

                # Ajuste columnas: dar más ancho a columnas con texto largo
                col_widths = [50, 150, 50, 150, 50, 70]

                table = Table(data, colWidths=col_widths)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#cce6ff")),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#003366")),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#003366")),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                ]))
                elements.append(table)
                elements.append(Spacer(1, 12))

            # Tratamientos
            treatments = RiskTreatment.objects.filter(risk=risk)
            if treatments.exists():
                elements.append(Paragraph("Tratamientos de Riesgo", heading_style))
                for treat in treatments:
                    elements.append(Paragraph(f"Acción: {treat.treatment_action}", normal_style))
                    responsible_names = ", ".join([pos.name for pos in treat.responsible.all()])
                    elements.append(Paragraph(f"Responsables: {responsible_names}", normal_style))
                    elements.append(Paragraph(f"Fecha Objetivo: {treat.target_date.strftime('%d/%m/%Y') if treat.target_date else '-'}", normal_style))
                    elements.append(Paragraph(f"Fecha Real: {treat.actual_date.strftime('%d/%m/%Y') if treat.actual_date else '-'}", normal_style))
                    elements.append(Spacer(1, 6))

            # Planes de contingencia
            contingency_plans = ContingencyPlan.objects.filter(risk=risk)
            if contingency_plans.exists():
                elements.append(Paragraph("Planes de Contingencia", heading_style))
                for plan in contingency_plans:
                    contingency_actions_display = plan.contingency_actions_display
                    elements.append(Paragraph("Acciones:", subheading_style))
                    actions_list = ListFlowable(
                        [ListItem(Paragraph(action, normal_style)) for action in contingency_actions_display],
                        bulletType='bullet',
                        leftIndent=15
                    )
                    elements.append(actions_list)

                    responsible_list = [pos.name for pos in plan.responsible.all()]
                    communicate_list = [pos.name for pos in plan.communicate_to.all()]

                    elements.append(Paragraph(f"Responsables: {', '.join(responsible_list) if responsible_list else '-'}", normal_style))
                    elements.append(Paragraph(f"Comunicar a: {', '.join(communicate_list) if communicate_list else '-'}", normal_style))
                    elements.append(Spacer(1, 12))

            # Reevaluaciones
            reevaluations = Reevaluation.objects.filter(risk=risk)
            if reevaluations.exists():
                elements.append(Paragraph("Reevaluaciones", heading_style))

                # Diccionario de traducción de niveles de riesgo
                risk_level_translation = {
                    'High': 'Alto',
                    'Moderate': 'Moderado',
                    'Low': 'Bajo'
                }

                reevaluation_data = [["Severidad", "Ocurrencia", "Detección", "Nivel de Riesgo"]]
                for reeval in reevaluations:
                    risk_level_color = {
                        'High': colors.HexColor("#d9534f"),
                        'Moderate': colors.HexColor("#f0ad4e"),
                        'Low': colors.HexColor("#5cb85c")
                    }.get(reeval.risk_level, colors.black)

                    translated_risk_level = risk_level_translation.get(reeval.risk_level, reeval.risk_level)

                    reevaluation_data.append([
                        str(reeval.severity),
                        str(reeval.occurrence),
                        str(reeval.detection),
                        Paragraph(f'<font color="{risk_level_color}"><b>{translated_risk_level}</b></font>', normal_style)
                    ])

                reevaluation_table = Table(reevaluation_data, colWidths=[60, 60, 60, 80])
                reevaluation_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#cce6ff")),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#003366")),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#003366")),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                ]))
                elements.append(reevaluation_table)
                elements.append(Spacer(1, 18))

            # Separador de riesgos (línea)
            elements.append(Spacer(1, 12))
            elements.append(Paragraph("-" * 110, normal_style))
            elements.append(Spacer(1, 18))

            # Salto de página: un riesgo por página
            if idx != len(risks):  # No poner PageBreak al final del último riesgo
                elements.append(PageBreak())

    # Pie de página con fecha y número de página
    def add_footer(canvas: Canvas, doc):
        canvas.saveState()
        footer_text = f"Generado el {date.today().strftime('%d/%m/%Y')} | Página {doc.page}"
        canvas.setFont("Helvetica-Oblique", 9)
        canvas.setFillColor(colors.grey)
        canvas.drawRightString(doc.pagesize[0] - 40, 20, footer_text)
        canvas.restoreState()

    doc.build(elements, onFirstPage=add_footer, onLaterPages=add_footer)
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f"reporte_riesgos_{area.name}.pdf")
