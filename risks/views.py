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


def create_risk(request, risk_id=None):
    success_message = None
    keep_modal_open = False

    risk_identifications = RiskIdentification.objects.all()
    risk_treatments = RiskTreatment.objects.all()
    contingency_plans = ContingencyPlan.objects.all()
    reevaluations = Reevaluation.objects.all()
    evaluations = RiskEvaluation.objects.select_related('risk_level').all()

    grouped_risks = defaultdict(list)
    for risk in risk_identifications:
        grouped_risks[risk.department.name].append(risk)

    risk = None
    if risk_id:
        risk = get_object_or_404(RiskIdentification, id=risk_id)

    # Si hay un ID en el POST, intentamos obtener el riesgo
    elif request.method == "POST":
        risk_id = request.POST.get("risk")  
        if risk_id:
            risk = RiskIdentification.objects.filter(id=risk_id).first()

    # Cargar instancias de los modelos relacionados si el riesgo existe
    evaluation = RiskEvaluation.objects.filter(risk=risk).first() if risk else None
    treatment = RiskTreatment.objects.filter(risk=risk).first() if risk else None
    contingency_plan = ContingencyPlan.objects.filter(risk=risk).first() if risk else None
    reevaluation = Reevaluation.objects.filter(risk=risk).first() if risk else None

    # Inicializar formularios
    form_create = RiskIdentificationForm(request.POST if "save_risk_identification" in request.POST else None, instance=risk)
    form_evaluation = RiskEvaluationForm(request.POST if "save_risk_evaluation" in request.POST else None, instance=evaluation)
    form_treatment = RiskTreatmentForm(request.POST if "save_risk_treatment" in request.POST else None, instance=treatment)
    form_contingency = ContingencyPlanForm(request.POST if "save_contingency_plan" in request.POST else None, instance=contingency_plan)
    form_reevaluation = ReevaluationForm(request.POST if "save_risk_reevaluation" in request.POST else None, instance=reevaluation)

    if request.method == "POST":
        if "save_risk_identification" in request.POST:
            if form_create.is_valid():
                risk = form_create.save()
                success_message = "Risk Identification saved successfully!"
                return redirect('dashboard-analytics', risk_id=risk.id)

        elif "save_risk_evaluation" in request.POST and risk:
            if form_evaluation.is_valid():
                evaluation = form_evaluation.save(commit=False)
                evaluation.risk = risk
                evaluation.save()
                success_message = "Risk Evaluation saved successfully!"

        elif "save_risk_treatment" in request.POST and risk:
            if form_treatment.is_valid():
                treatment = form_treatment.save(commit=False)
                treatment.risk = risk
                treatment.save()
                success_message = "Risk Treatment saved successfully!"

        elif "save_contingency_plan" in request.POST and risk:
            if form_contingency.is_valid():
                contingency_plan = form_contingency.save(commit=False)
                contingency_plan.risk = risk
                contingency_plan.save()
                success_message = "Contingency Plan saved successfully!"

        elif "save_risk_reevaluation" in request.POST and risk:
            if form_reevaluation.is_valid():
                reevaluation = form_reevaluation.save(commit=False)
                reevaluation.risk = risk
                reevaluation.save()
                success_message = "Risk Reevaluation saved successfully!"

        keep_modal_open = True

    return render(
        request,
        'dashboards/dashboard-analytics.html',
        {
            'risk_identifications': risk_identifications,
            'risk_treatments': risk_treatments,
            'contingency_plans': contingency_plans,
            'reevaluations': reevaluations,
            'evaluations': evaluations,
            'form_create': form_create,
            'form_evaluation': form_evaluation,
            'form_treatment': form_treatment,
            'form_contingency': form_contingency,
            'form_reevaluation': form_reevaluation,
            'success_message': success_message,
            'keep_modal_open': keep_modal_open,
            "grouped_risks": dict(grouped_risks),
            "risk": risk,
        }
    )



def generate_risks_pdf(request, department_name):
    department = get_object_or_404(Department, name=department_name)
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
    elements = []
    styles = getSampleStyleSheet()
    bold_style = ParagraphStyle(name='Bold', fontName='Helvetica-Bold', fontSize=12)
    normal_style = styles["BodyText"]

    elements.append(Paragraph(f"Risk Report - {department.name}", styles["Title"]))
    elements.append(Spacer(1, 12))

    risks = RiskIdentification.objects.filter(department=department)

    if not risks.exists():
        elements.append(Paragraph("No risks found for this department.", normal_style))
    else:
        for idx, risk in enumerate(risks, start=1):  # Numerar los riesgos
            try:
                risk_name = str(risk.identified_risk).replace('<', '&lt;').replace('>', '&gt;')
                elements.append(Paragraph(f"Risk #{idx}: {risk_name}", bold_style))
                elements.append(Paragraph(f"Activity Name: {risk.activity_name}", normal_style))
                elements.append(Paragraph(f"Consequences: {risk.consequences}", normal_style))
                elements.append(Spacer(1, 12))  # Espaciado aumentado entre riesgos

                # Paso 1 - Evaluaciones de Riesgo
                evaluations = RiskEvaluation.objects.filter(risk=risk)
                if evaluations.exists():
                    elements.append(Paragraph("Risk Evaluations:", styles["Heading4"]))
                    eval_data = [["Severity", "Preventive Controls", "Occurrence", "Detection Controls", "Detection", "Risk Level"]]
                    for eval in evaluations:
                        eval_data.append([
                            eval.severity,
                            "\n".join(eval.current_preventive_controls.split(", ")),  # Cada control en una línea
                            eval.occurrence,
                            "\n".join(eval.current_detection_controls.split(", ")),  # Cada control en una línea
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
                        ('WORDWRAP', (0, 0), (-1, -1), True),  # Ajustar texto que excede
                    ]))
                    elements.append(eval_table)
                    elements.append(Spacer(1, 10))  # Espaciado entre tablas

                # Paso 2 - Tratamiento de Riesgo
                treatments = RiskTreatment.objects.filter(risk=risk)
                if treatments.exists():
                    elements.append(Paragraph("Risk Treatments:", styles["Heading4"]))
                    treat_data = [["Treatment Action", "Responsible", "Target Date", "Actual Date"]]
                    for treat in treatments:
                        treat_data.append([
                            treat.treatment_action,
                            "\n".join(role.name for role in treat.responsible.all()),  # Cada responsable en una línea
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
                        ('WORDWRAP', (0, 0), (-1, -1), True),  # Ajustar texto que excede
                    ]))
                    elements.append(treat_table)
                    elements.append(Spacer(1, 10))  # Espaciado entre tablas

                # Paso 3 - Plan de Contingencia
                contingency_plans = ContingencyPlan.objects.filter(risk=risk)
                if contingency_plans.exists():
                    elements.append(Paragraph("Contingency Plans:", styles["Heading4"]))
                    contingency_data = [["Contingency Actions", "Responsible", "Communicate To"]]
                    for plan in contingency_plans:
                        contingency_data.append([
                            "\n".join(plan.contingency_actions.values_list('name', flat=True)),  # Cada acción en una línea
                            "\n".join(plan.responsible.values_list('name', flat=True)),  # Cada responsable en una línea
                            "\n".join(plan.communicate_to.values_list('name', flat=True)),  # Cada comunicado en una línea
                        ])
                    contingency_table = Table(contingency_data, colWidths=[180, 100, 100], repeatRows=1)
                    contingency_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('FONTSIZE', (0, 0), (-1, -1), 10),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('WORDWRAP', (0, 0), (-1, -1), True),  # Ajustar texto que excede
                    ]))
                    elements.append(contingency_table)
                    elements.append(Spacer(1, 10))  # Espaciado entre tablas

                # Paso 4 - Reevaluación
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
                        ('WORDWRAP', (0, 0), (-1, -1), True),  # Ajustar texto que excede
                    ]))
                    elements.append(reevaluation_table)
                    elements.append(Spacer(1, 12))  # Espaciado entre tablas

                elements.append(PageBreak())  # Añadir un salto de página al final de cada riesgo

            except Exception as e:
                elements.append(Paragraph(f"Error processing risk: {e}", normal_style))
    
    # Pie de página sin estilo
    def add_footer(canvas, doc):
        canvas.saveState()
        footer_text = f"Generated on {date.today()} | Page {doc.page}"
        canvas.setFont("Helvetica", 10)
        width = doc.width
        # Estilo del pie de página sin fondo ni color
        canvas.drawString(10, 10, footer_text)  # Texto simple
        canvas.restoreState()

    doc.build(elements, onFirstPage=add_footer, onLaterPages=add_footer)
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f"risks_{department.name}.pdf")



def save_risk_step(request, step):
    if request.method == "POST":
        print("Datos recibidos:", request.POST)  # Ver qué datos llegan al servidor

        risk_id = request.POST.get("risk_id")
        risk = None
        if risk_id:
            risk = get_object_or_404(RiskIdentification, id=risk_id)

        form = None

        if step == 1:
            form = RiskIdentificationForm(request.POST, instance=risk)  # Usar la instancia para editar
        elif step == 2:
            form = RiskEvaluationForm(request.POST, instance=RiskEvaluation.objects.filter(risk=risk).first())
        elif step == 3:
            form = RiskTreatmentForm(request.POST, instance=RiskTreatment.objects.filter(risk=risk).first())
        elif step == 4:
            form = ContingencyPlanForm(request.POST, instance=ContingencyPlan.objects.filter(risk=risk).first())
        elif step == 5:
            form = ReevaluationForm(request.POST, instance=Reevaluation.objects.filter(risk=risk).first())

        if form:
            if form.is_valid():
                form.save()
                return JsonResponse({"success": True})
            else:
                print("Errores del formulario:", form.errors)  # Ver los errores de validación
                return JsonResponse({"success": False, "error": form.errors}, status=400)
        else:
            print("No se encontró el formulario para el paso", step)

    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)



def get_risk_data(request, risk_id):
    """Obtiene los datos de un riesgo y devuelve los formularios renderizados."""
    risk = get_object_or_404(RiskIdentification, id=risk_id)

    # Obtener las instancias correctas para cada formulario
    evaluation = RiskEvaluation.objects.filter(risk=risk).first()
    treatment = RiskTreatment.objects.filter(risk=risk).first()
    contingency = ContingencyPlan.objects.filter(risk=risk).first()
    reevaluation = Reevaluation.objects.filter(risk=risk).first()

    # Inicializar formularios con sus respectivas instancias
    form_create = RiskIdentificationForm(instance=risk)
    form_evaluation = RiskEvaluationForm(instance=evaluation)  # Corregido
    form_treatment = RiskTreatmentForm(instance=treatment)  # Corregido
    form_contingency = ContingencyPlanForm(instance=contingency)  # Corregido
    form_reevaluation = ReevaluationForm(instance=reevaluation)  # Corregido

    # Renderizar los formularios como HTML
    form_create_html = render_to_string('dashboards/form_create.html', {'form': form_create})
    form_evaluation_html = render_to_string('dashboards/form_evaluation.html', {'form': form_evaluation})
    form_treatment_html = render_to_string('dashboards/form_treatment.html', {'form': form_treatment})
    form_contingency_html = render_to_string('dashboards/form_contingency.html', {'form': form_contingency})
    form_reevaluation_html = render_to_string('dashboards/form_reevaluation.html', {'form': form_reevaluation})

    data = {
        "id": risk.id,
        "identified_risk": risk.identified_risk,
        "form_create": form_create_html,
        "form_evaluation": form_evaluation_html,
        "form_treatment": form_treatment_html,
        "form_contingency": form_contingency_html,
        "form_reevaluation": form_reevaluation_html,
    }

    return JsonResponse(data)



def update_risk(request, risk_id, step):
    """Actualiza los datos de un riesgo en función del paso del formulario."""
    risk = get_object_or_404(RiskIdentification, id=risk_id)

    if request.method == "POST":
        step = int(step)  # Asegurar que sea un número entero

        form_classes = [
            RiskIdentificationForm,
            RiskEvaluationForm,
            RiskTreatmentForm,
            ContingencyPlanForm,
            ReevaluationForm
        ]

        if 1 <= step <= 5:
            form = form_classes[step - 1](request.POST, instance=risk)
        else:
            return JsonResponse({"success": False, "error": "Paso no válido"}, status=400)

        if form.is_valid():
            form.save()
            return JsonResponse({"success": True, "message": "Datos actualizados correctamente"})
        else:
            return JsonResponse({"success": False, "errors": form.errors}, status=400)

    return JsonResponse({"success": False, "error": "Método no permitido"}, status=405)


