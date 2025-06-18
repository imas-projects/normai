from django.shortcuts import render, redirect, get_object_or_404
from .models import RiskIdentification, RiskEvaluation, RiskTreatment, ContingencyPlan, Reevaluation
from .forms import RiskIdentificationForm, RiskEvaluationForm, RiskTreatmentForm, ContingencyPlanForm, ReevaluationForm
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
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

from ai_functions.monitoring_functions import suggest_risk_fields, suggest_controls, suggest_rating_ranges, suggest_risk_level, suggest_treatment_action

def create_risk(request):
    all_risks = RiskIdentification.objects.select_related('area').all() 

    grouped_risks = {}
    for risk in all_risks:
        area = risk.area 
        if area not in grouped_risks:
            grouped_risks[area] = []
        grouped_risks[area].append(risk)

    evaluations = RiskEvaluation.objects.select_related('risk').all()
    treatments = RiskTreatment.objects.select_related('risk').all()
    contingency_plans = ContingencyPlan.objects.select_related('risk').all()
    reevaluations = Reevaluation.objects.select_related('risk').all()

    return render(request, 'mistemplates/risks.html', {
        'grouped_risks': grouped_risks,
        'evaluations': evaluations,
        'treatments': treatments,
        'contingency_plans': contingency_plans,
        'reevaluations': reevaluations,
    })

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

def get_suggestions(request):
    area_id = request.GET.get('area')
    activity_name = request.GET.get('activity_name')

    if not area_id or not activity_name:
        return JsonResponse({'error': 'Faltan parámetros'}, status=400)

    try:
        area_obj = Area.objects.get(id=area_id)
        area_name = area_obj.name
    except Area.DoesNotExist:
        return JsonResponse({'error': 'Área no encontrada'}, status=404)

    suggestions = suggest_risk_fields(area_name, activity_name)

    if not suggestions or not isinstance(suggestions, list):
        return JsonResponse({'error': 'No se encontraron sugerencias'}, status=404)

    return JsonResponse(suggestions, safe=False)


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


def add_risk_treatment(request):
    if request.method == 'POST':
        form = RiskTreatmentForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({'message': 'Tratamiento de riesgo guardado correctamente'}, status=200)
        else:
            return JsonResponse({'error': form.errors}, status=400)
    else:
        form = RiskTreatmentForm()

    return render(request, 'mistemplates/add_risk_treatment.html', {'form': form})

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


def add_contingency_plan(request):
    if request.method == 'POST':
        form = ContingencyPlanForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({'message': 'Contingency plan saved successfully'}, status=200)  
        else:
            return JsonResponse({'error': form.errors}, status=400)
    else:
        form = ContingencyPlanForm()

    return render(request, 'mistemplates/add_contingency_plan.html', {'form': form})

def add_reevaluation(request):
    if request.method == 'POST':
        form = ReevaluationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('risks:risks')
    else:
        form = ReevaluationForm()

    return render(request, 'mistemplates/add_reevaluation.html', {'form': form})

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

def generate_risks_pdf(request, area_name): 
    area = get_object_or_404(Area, name=area_name)  
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
    elements = []
    styles = getSampleStyleSheet()
    bold_style = ParagraphStyle(name='Bold', fontName='Helvetica-Bold', fontSize=12)
    normal_style = styles["BodyText"]

    elements.append(Paragraph(f"Risk Report - {area.name}", styles["Title"]))  
    elements.append(Spacer(1, 12))

    risks = RiskIdentification.objects.filter(area=area) 

    if not risks.exists():
        elements.append(Paragraph("No risks found for this area.", normal_style))  
    else:
        for idx, risk in enumerate(risks, start=1):  
            try:
                risk_name = str(risk.identified_risk).replace('<', '&lt;').replace('>', '&gt;')
                elements.append(Paragraph(f"Risk #{idx}: {risk_name}", bold_style))
                elements.append(Paragraph(f"Activity Name: {risk.activity_name}", normal_style))
                elements.append(Paragraph(f"Consequences: {risk.consequences}", normal_style))
                elements.append(Spacer(1, 12))  

                evaluations = RiskEvaluation.objects.filter(risk=risk)
                if evaluations.exists():
                    elements.append(Paragraph("Risk Evaluations:", styles["Heading4"]))
                    eval_data = [["Severity", "Preventive Controls", "Occurrence", "Detection Controls", "Detection", "Risk Level"]]
                    for eval in evaluations:
                        eval_data.append([
                            eval.severity,
                            "\n".join(eval.current_preventive_controls.split(", ")),  
                            eval.occurrence,
                            "\n".join(eval.current_detection_controls.split(", ")),  
                            eval.detection,
                            eval.risk_level.level
                        ])
                    eval_table = Table(eval_data, colWidths=[80, 100, 80, 100, 80, 80], repeatRows=1)
                    eval_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('FONTSIZE', (0, 0), (-1, -1), 10),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('WORDWRAP', (0, 0), (-1, -1), True),  
                    ]))
                    elements.append(eval_table)
                    elements.append(Spacer(1, 10))  

                treatments = RiskTreatment.objects.filter(risk=risk)
                if treatments.exists():
                    elements.append(Paragraph("Risk Treatments:", styles["Heading4"]))
                    treat_data = [["Treatment Action", "Responsible", "Target Date", "Actual Date"]]
                    for treat in treatments:
                        treat_data.append([
                            treat.treatment_action,
                            "\n".join(role.name for role in treat.responsible.all()),  
                            treat.target_date.strftime('%Y-%m-%d') if treat.target_date else '',
                            treat.actual_date.strftime('%Y-%m-%d') if treat.actual_date else '',
                        ])
                    treat_table = Table(treat_data, colWidths=[180, 100, 80, 80], repeatRows=1)
                    treat_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('FONTSIZE', (0, 0), (-1, -1), 10),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('WORDWRAP', (0, 0), (-1, -1), True),
                    ]))
                    elements.append(treat_table)
                    elements.append(Spacer(1, 10))
                    
                contingency_plans = ContingencyPlan.objects.filter(risk=risk)
                if contingency_plans.exists():
                    elements.append(Paragraph("Contingency Plans:", styles["Heading4"]))
                    contingency_data = [["Contingency Actions", "Responsible", "Communicate To"]]
                    for plan in contingency_plans:
                        contingency_data.append([
                            "\n".join(plan.contingency_actions.values_list('name', flat=True)),  
                            "\n".join(plan.responsible.values_list('name', flat=True)),  
                            "\n".join(plan.communicate_to.values_list('name', flat=True)),  
                        ])
                    contingency_table = Table(contingency_data, colWidths=[180, 100, 100], repeatRows=1)
                    contingency_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('FONTSIZE', (0, 0), (-1, -1), 10),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('WORDWRAP', (0, 0), (-1, -1), True),  
                    ]))
                    elements.append(contingency_table)
                    elements.append(Spacer(1, 10))  

                reevaluations = Reevaluation.objects.filter(risk=risk)
                if reevaluations.exists():
                    elements.append(Paragraph("Reevaluations:", styles["Heading4"]))
                    reevaluation_data = [["Severity", "Occurrence", "Detection", "Risk Level"]]
                    for reeval in reevaluations:
                        reevaluation_data.append([
                            reeval.severity, reeval.occurrence, reeval.detection, reeval.risk_level.level,
                        ])
                    reevaluation_table = Table(reevaluation_data, colWidths=[80, 60, 60, 80], repeatRows=1)
                    reevaluation_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('FONTSIZE', (0, 0), (-1, -1), 10),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('WORDWRAP', (0, 0), (-1, -1), True),  
                    ]))
                    elements.append(reevaluation_table)
                    elements.append(Spacer(1, 12))  

                elements.append(PageBreak())  

            except Exception as e:
                elements.append(Paragraph(f"Error processing risk: {e}", normal_style))
    
    def add_footer(canvas, doc):
        canvas.saveState()
        footer_text = f"Generated on {date.today()} | Page {doc.page}"
        canvas.setFont("Helvetica", 10)
        width = doc.width
        canvas.drawString(10, 10, footer_text)
        canvas.restoreState()

    doc.build(elements, onFirstPage=add_footer, onLaterPages=add_footer)
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f"risks_{area.name}.pdf") 
