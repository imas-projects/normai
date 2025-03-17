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

    risk = get_object_or_404(RiskIdentification, id=risk_id) if risk_id else None

    evaluation = RiskEvaluation.objects.filter(risk=risk).first() if risk else None
    treatment = RiskTreatment.objects.filter(risk=risk).first() if risk else None
    contingency_plan = ContingencyPlan.objects.filter(risk=risk).first() if risk else None
    reevaluation = Reevaluation.objects.filter(risk=risk).first() if risk else None

    form_create = RiskIdentificationForm(instance=risk)
    form_evaluation = RiskEvaluationForm(instance=evaluation)
    form_treatment = RiskTreatmentForm(instance=treatment)
    form_contingency = ContingencyPlanForm(instance=contingency_plan)
    form_reevaluation = ReevaluationForm(instance=reevaluation)

    if request.method == "POST":
        response_data = {}

        if "save_risk_identification" in request.POST:
            form_create = RiskIdentificationForm(request.POST, instance=risk)
            if form_create.is_valid():
                risk = form_create.save()
                success_message = "Risk Identification saved successfully!"
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'message': success_message, 'reload': True})
                return redirect('mistemplates/dashboard-analytics')

        elif "save_risk_evaluation" in request.POST:
            form_evaluation = RiskEvaluationForm(request.POST, instance=evaluation)
            if risk and form_evaluation.is_valid():
                evaluation = form_evaluation.save(commit=False)
                evaluation.risk = risk
                evaluation.save()
                success_message = "Risk Evaluation saved successfully!"
                return JsonResponse({'message': success_message})
            else:
                return JsonResponse({'error': form_evaluation.errors}, status=400)

        elif "save_risk_treatment" in request.POST:
            form_treatment = RiskTreatmentForm(request.POST, instance=treatment)
            if risk and form_treatment.is_valid():
                treatment = form_treatment.save(commit=False)
                treatment.risk = risk
                treatment.save()
                success_message = "Risk Treatment saved successfully!"
                return JsonResponse({'message': success_message})
            else:
                return JsonResponse({'error': form_treatment.errors}, status=400)

        elif "save_contingency_plan" in request.POST:
            form_contingency = ContingencyPlanForm(request.POST, instance=contingency_plan)
            if risk and form_contingency.is_valid():
                contingency_plan = form_contingency.save(commit=False)
                contingency_plan.risk = risk
                contingency_plan.save()
                success_message = "Contingency Plan saved successfully!"
                return JsonResponse({'message': success_message})
            else:
                return JsonResponse({'error': form_contingency.errors}, status=400)

        elif "save_risk_reevaluation" in request.POST:
            form_reevaluation = ReevaluationForm(request.POST, instance=reevaluation)
            if risk and form_reevaluation.is_valid():
                reevaluation = form_reevaluation.save(commit=False)
                reevaluation.risk = risk
                reevaluation.save()
                success_message = "Risk Reevaluation saved successfully!"
                return JsonResponse({'message': success_message, 'reload': True})
            else:
                return JsonResponse({'error': form_reevaluation.errors}, status=400)

        return JsonResponse({'error': 'Invalid request'}, status=400)

    return render(
        request,
        'mistemplates/risks.html',
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
    return FileResponse(buffer, as_attachment=True, filename=f"risks_{department.name}.pdf")





@csrf_protect  
def save_risk_step(request, step):
    if request.method == "POST":
        print("Datos recibidos:", request.POST)  

        risk_id = request.POST.get("risk") 
        risk = None
        if risk_id:
            risk = get_object_or_404(RiskIdentification, id=risk_id)

        form = None

        if step == 1:
            form = RiskIdentificationForm(request.POST, instance=risk)  
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
                print("Errores del formulario:", form.errors)  
                return JsonResponse({"success": False, "error": form.errors}, status=400)
        else:
            print("No se encontró el formulario para el paso", step)

    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)



def get_risk_data(request, risk_id):
    """Obtiene los datos de un riesgo y devuelve los formularios renderizados."""
    risk = get_object_or_404(RiskIdentification, id=risk_id)

    evaluation = RiskEvaluation.objects.filter(risk=risk).first()
    treatment = RiskTreatment.objects.filter(risk=risk).first()
    contingency = ContingencyPlan.objects.filter(risk=risk).first()
    reevaluation = Reevaluation.objects.filter(risk=risk).first()

    form_create = RiskIdentificationForm(instance=risk)
    form_evaluation = RiskEvaluationForm(instance=evaluation)  
    form_treatment = RiskTreatmentForm(instance=treatment)  
    form_contingency = ContingencyPlanForm(instance=contingency)  
    form_reevaluation = ReevaluationForm(instance=reevaluation)  

    form_create_html = render_to_string('mistemplates/form_create.html', {'form': form_create})
    form_evaluation_html = render_to_string('mistemplates/form_evaluation.html', {'form': form_evaluation})
    form_treatment_html = render_to_string('mistemplates/form_treatment.html', {'form': form_treatment})
    form_contingency_html = render_to_string('mistemplates/form_contingency.html', {'form': form_contingency})
    form_reevaluation_html = render_to_string('mistemplates/form_reevaluation.html', {'form': form_reevaluation})

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

