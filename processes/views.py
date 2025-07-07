from django.shortcuts import render, redirect, get_object_or_404
from .models import Process
from django.contrib.auth.models import User
from .forms import ProcessForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Process, ProcessInput, PerformanceIndicator, ProcessMeasurement, ProcessOutput, Documentation, ProcessActivity, ProcessPosition, ProductMeasurement,ProcessPerformanceMeasurements, ProcessPerformanceIndicators
from company.models import ExternalClient, ExternalSupplier, Area, Position
from django.http import JsonResponse
import json
import datetime
from datetime import date, timedelta
from django.db.models.functions import TruncMonth
from django.db.models import Count, Avg, F, Q
from collections import OrderedDict

@login_required
def list_processes(request):
    processes = Process.objects.all().order_by('name')

    # === Gráfico: Número de Alertas Por Proceso ===
    todos_documentos = Documentation.objects.all().order_by('-id')[:5]
    todos_procesos = Process.objects.all()
    hoy = date.today()
    ultimo_mes = hoy - timedelta(days=30)

    process_labels = [proceso.name for proceso in todos_procesos]

    recientes_process_perform_measure = ProcessPerformanceMeasurements.objects.filter(date__gte=ultimo_mes)
    alerta = []
    procesos_alerta = []

    for ppm in recientes_process_perform_measure:
        indicador = ProcessPerformanceIndicators.objects.get(
            process=ppm.process,
            performanceindicator=ppm.performance_indicator
        )

        min_val = indicador.min_acceptable_value
        max_val = indicador.max_acceptable_value

        if ((min_val is not None and ppm.measured_value < min_val) or
            (max_val is not None and ppm.measured_value > max_val)):
            
            alerta.append(ppm)
            procesos_alerta.append(ppm.process.name)
        
        proceso_numero_alertas = {}
        for nombre in procesos_alerta:
            if nombre in proceso_numero_alertas:
                proceso_numero_alertas[nombre] += 1
            else:
                proceso_numero_alertas[nombre] = 1
        procesos_con_alertas = list(proceso_numero_alertas.keys())

        for proceso in Process.objects.all():
            if proceso.name not in proceso_numero_alertas:
                proceso_numero_alertas[proceso.name] = 0.01

    process_labels=list(proceso_numero_alertas.keys()) 
    process_values=list(proceso_numero_alertas.values())

            

    return render(request, 'mistemplates/processes.html', {'processes': processes, 'process_labels':process_labels,'process_values':process_values, 'todos_documentos':todos_documentos})

@login_required
def create_process(request):
    if request.method == 'POST':
        form = ProcessForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Process created successfully.')
            return redirect('processes:list_processes') 
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProcessForm()
    return render(request, 'mistemplates/create_process.html', {'form': form})

@login_required
def load_form_options(request):
    responsible_options = list(Position.objects.all().values('id', 'name'))
    internal_suppliers_options = list(Area.objects.all().values('id', 'name'))
    external_suppliers_options = list(ExternalSupplier.objects.all().values('id', 'name'))
    internal_clients_options = list(Area.objects.all().values('id', 'name'))
    external_clients_options = list(ExternalClient.objects.all().values('id', 'name'))
    inputs_options= list(ProcessInput.objects.all().values('id', 'name'))
    outputs_options= list(ProcessOutput.objects.all().values('id', 'name'))
    documents_options= list(Documentation.objects.all().values('id', 'document_description','document_code'))
    #measurements_options= list(ProcessMeasurement.objects.all().values('id','measurement_process_parameter'))
    #indicators_options= list(PerformanceIndicator.objects.all().values('id', 'name'))
    activities_options=list(ProcessActivity.objects.all().values('id','activity','order'))

    return {
        'responsible_options' : responsible_options,
        'internal_suppliers_options' : internal_suppliers_options,
        'external_suppliers_options' : external_suppliers_options,
        'internal_clients_options' : internal_clients_options,
        'external_clients_options' : external_clients_options,
        'inputs_options' : inputs_options,
        'outputs_options' : outputs_options,
        'documents_options' : documents_options,
        'activities_options':activities_options,
        #'indicators_options' : indicators_options,
        #'measurements_options' : measurements_options,
    }

@login_required
def get_process(request, id):
    try:
        current_process = Process.objects.get(id=id)

        current_process_internal_suppliers = list(current_process.internal_suppliers.all().values('id', 'name'))
        current_process_external_suppliers = list(current_process.external_suppliers.all().values('id', 'name'))
        current_process_internal_clients = list(current_process.internal_clients.all().values('id', 'name')) 
        current_process_external_clients = list(current_process.external_clients.all().values('id', 'name'))
        current_process_inputs = list(current_process.inputs.all().values('id', 'name'))
        current_process_outputs = list(current_process.outputs.all().values('id', 'name'))
        current_process_documents = list(current_process.documents.all().values('id', 'document_description','document_code'))

        current_activites = ProcessActivity.objects.filter(process_id=id)
        activities = list(current_activites.all().values('id','activity','order'))

        current_process_indicators = list(current_process.performance_indicators.all().values('id', 'name'))
        
        form_options = load_form_options(request)

        return JsonResponse({
            'success': True, 
            # Campos unicos o foreign key
            'id': current_process.id,
            'name' : current_process.name,
            'objective': current_process.objective,
            'responsible': current_process.responsible.id,
            #'review': current_process.review,
            #'review_date': current_process.review_date,
            #'staff_roles': current_process.staff_roles,
            #'workspaces': current_process.workspaces,
            #'facilities': current_process.facilities,
            #'equipment': current_process.equipment,
            #'materials': current_process.materials,
            #'transport_resources': current_process.transport_resources,
            #'communication_technologies': current_process.communication_technologies,
            #'operational_environment': current_process.operational_environment,

            # Campos manytomany
            'internal_suppliers': current_process_internal_suppliers,
            'external_suppliers': current_process_external_suppliers,
            'internal_clients':current_process_internal_clients,
            'external_clients':current_process_external_clients,
            'inputs' : current_process_inputs,
            'outputs' : current_process_outputs,
            'documents': current_process_documents,
            'activities':activities,
            'indicators' : current_process_indicators,
           

            # Opciones formulario
            **form_options,
        })
    except Process.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Row not found.'})

@login_required
def update_process(request):
    if request.method == 'POST':
            data = json.loads(request.body)
            try:
                process_id = data.get('id')
                process_name = data.get('process_name')
                process_objective = data.get('process_objective')
                process_review_date = datetime.date.today()
                process_responsible= data.get('process_responsible')

                process_staff_roles = data.get('process_staff_roles')
                process_workspaces = data.get('process_workspaces')
                process_facilities = data.get('process_facilities')
                process_equipment = data.get('process_equipment')
                process_materials = data.get('process_materials')
                process_transport_resources = data.get('process_transport_resources')
                process_communication_technologies = data.get('process_communication_technologies')
                process_operational_environment = data.get('process_operational_environment')

                selected_internal_suppliers = [int(id) for id in data.get('process_internal_suppliers', [])]
                selected_external_suppliers = [int(id) for id in data.get('process_external_suppliers', [])]
                selected_inputs = [int(id) for id in data.get('process_inputs', [])]
                selected_outputs = [int(id) for id in data.get('process_outputs', [])]
                selected_internal_clients = [int(id) for id in data.get('process_internal_clients', [])]
                selected_external_clients = [int(id) for id in data.get('process_external_clients', [])]
                selected_documents = [int(id) for id in data.get('process_documents', [])]
                #selected_activities = [int(id) for id in  data.get('process_activities', [])]
                #selected_indicators = data.get('process_indicators', [])

                updated_process = Process.objects.get(id=process_id)
                updated_process.name = process_name
                updated_process.objective = process_objective
                updated_process.review_date = process_review_date
                updated_process.responsible = Position.objects.get(id=process_responsible) 

                updated_process.internal_suppliers.set(selected_internal_suppliers)
                updated_process.external_suppliers.set(selected_external_suppliers)
                updated_process.inputs.set(selected_inputs)
                updated_process.outputs.set(selected_outputs)
                updated_process.internal_clients.set(selected_internal_clients)
                updated_process.external_clients.set(selected_external_clients)
                updated_process.documents.set(selected_documents)

                #print(selected_activities)
                #for s in selected_activities:
                #    ProcessActivity.objects.create(process_id=process_id,order=contador,activity=texto)


                #updated_process.performance_indicators.set(selected_indicators)

                updated_process.save()
                return JsonResponse({'success': True})
            except Exception as e:
                import traceback
                traceback.print_exc()
                return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid method'})

@login_required
def edit_process(request, process_id):
    process = get_object_or_404(Process, id=process_id)
    if request.method == 'POST':
        form = ProcessForm(request.POST, instance=process)
        if form.is_valid():
            form.save()
            return JsonResponse({'message': 'Process updated successfully'}, status=200)
        else:
            return JsonResponse({'errors': form.errors}, status=400)
    else:
        form = ProcessForm(instance=process)
        
    return render(request, 'mistemplates/edit_process.html', {'form': form, 'process': process})

from risks.models import RiskIdentification
@login_required
def add_risk_processes(request):
    processes = Process.objects.all()

    if request.method == "POST":
        form_name = request.POST.get("form_name")

        if form_name == "add_risk_processes_form" :
            process_id = request.POST.get("process_id")
            process_name = request.POST.get("process_name")
            process_risk = request.POST.get("process_risk")
            process_consequence = request.POST.get("process_consequence")
            process_area_id = 9

            new_risk_process = RiskIdentification.objects.create(
                activity_name = process_name,
                identified_risk = process_risk,
                consequences = process_consequence,
                area_id = process_area_id
            )

            new_risk_process.save

    return render(request, 'mistemplates/processes.html', {'processes': processes})

@login_required
def save_process_summarize_ia(request):

    if request.method == "POST":
        form_name = request.POST.get("form_name")

        if form_name == "save_process_summarize_form" :
            process_id = request.POST.get("process_id")
            new_summary = request.POST.get("summary")

            updated_process = Process.objects.get(id=process_id)
            updated_process.summary=new_summary[:1000]
            updated_process.save() 


    return redirect('processes:list_processes')

@login_required
def kpis_processes(request):
    processes = Process.objects.all()

    process_perform_measure = ProcessPerformanceMeasurements.objects.all()

    qs = (
        ProcessPerformanceMeasurements.objects
        .annotate(month=TruncMonth('date'))
        .values('performance_indicator__name', 'month', 'measured_value', 'date')
        .order_by('performance_indicator__name', 'month', 'date')
    )

    months = sorted({row['month'] for row in qs})
    month_labels = [m.strftime('%Y-%m') for m in months]

    data = OrderedDict()
    for row in qs:
        name = row['performance_indicator__name']
        mon  = row['month'].strftime('%Y-%m')
        val  = float(row['measured_value'])

        if name not in data:
            data[name] = OrderedDict()

        data[name][mon] = val


    for series in data.values():
        for m in month_labels:
            series.setdefault(m, None)

    # 5) Prepara las listas para el gráfico
    kpi_labels = list(data.keys())
    kpi_series = [list(series.values()) for series in data.values()]

        
    return render(request, 'mistemplates/kpis-processes.html', 
                  {'processes': processes,
                   'process_perform_measure':process_perform_measure,
                    'month_labels': month_labels,
                    'kpi_labels'  : kpi_labels,
                    'kpi_series'  : kpi_series,

                   })

@login_required
def save_kpi_processes(request):
    if request.method == "POST":
        form_name = request.POST.get("form_name")

        if form_name == "save_kpi_processes_form" :
            process_id = request.POST.get("process_id")
            new_kpi = request.POST.get("kpi_name")
            new_kpi_is_effective = request.POST.get("kpi_is_effective")
            new_kpi_is_efficient = request.POST.get("kpi_is_efficient")

            kpi = PerformanceIndicator.objects.create(
                name = new_kpi,
                effective = new_kpi_is_effective,
                efficient = new_kpi_is_efficient
            )

            updated_process = Process.objects.get(id=process_id)
            updated_process.performance_indicators.add(kpi)

    return redirect('processes:kpis_processes')

############## Views con IA

from ai_functions import implementation_functions as ai


def kpis_detector_ia(request):
    processes = Process.objects.all()
    assistant_answer = None

    json_function_name = "kpis_detector_function"
    json_function_description = "This function should identify 1 or more KPI in a process" \
                                "of a manufacturing plant according to ISO 9001:2015 norm and the given data."
    json_schema_input = {
    "type": "object",
    "properties": {
        "detected_kpi": {
            "type": "array",
            "description": "A list of identified KPIs with descriptions and if it could be efficient or effective.",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Indicates a possible identified KPI."
                    },
                    "efficient": {
                        "type": "boolean",
                        "description": "True if the KPI could be efficient"
                    },
                    "effective": {
                        "type": "boolean",
                        "description": "True if the KPI could be effective"
                    }
                },
                "required": [
                    "name",
                    "effective",
                    "efficient",
                ],
                "additionalProperties": False
            },
        }
    },
    "required": ["detected_kpi"],
    "additionalProperties": False,
    "strict": False,
    "stream":True,
    }

    if request.method == "POST":
        form_name = request.POST.get("form_name")

        if form_name == "kpis-detector_form" :
            process_id = int(request.POST.get("process_id"))

            process= Process.objects.get(id=process_id)
            activities = process.processactivity_set.all().order_by("order")
            activity_list = "\n".join([f"{a.order}. {a.activity}" for a in activities])

            process_data = f"""
                Estos son los datos del proceso:
                Nombre: {process.name}
                Objetivo: {process.objective}
                Pasos del proceso: {activity_list or "No especificados"}

                Espacios de trabajo: {process.workspaces or "No especificados"}
                Instalaciones: {process.facilities or "No especificadas"}
                Equipamiento: {process.equipment or "No especificado"}
                Materiales: {process.materials or "No especificados"}
                Recursos de transporte: {process.transport_resources or "No especificados"}
                Tecnologías de comunicación: {process.communication_technologies or "No especificadas"}
                Entorno operativo: {process.operational_environment or "No especificado"}

                Proveedores internos: {", ".join([a.name for a in process.internal_suppliers.all()]) or "Ninguno"}
                Proveedores externos: {", ".join([e.name for e in process.external_suppliers.all()]) or "Ninguno"}
                Clientes internos: {", ".join([a.name for a in process.internal_clients.all()]) or "Ninguno"}
                Clientes externos: {", ".join([e.name for e in process.external_clients.all()]) or "Ninguno"}

                Entradas del proceso: {", ".join([i.name for i in process.inputs.all()]) or "Ninguna"}
                Salidas del proceso: {", ".join([o.name for o in process.outputs.all()]) or "Ninguna"}
                Documentación: {", ".join([d.document_description for d in process.documents.all()]) or "Ninguna"}
                KPIs actuales: {", ".join([i.name for i in process.performance_indicators.all()]) or "Ninguno"}
                """
            
            user_input = "Identify at least 1 specific and meaningful KPI, different from the ones that the procees already has, focusing mainly on the provided process data. Use the ISO 9001:2015 standard only as a supporting framework to validate or guide your reasoning."\
                        "Your response must reflect the unique characteristics of the process and not rely on generic assumptions. Structure the result as a list of KPIs."

            assistant_answer = ai.ai_json_function(process_data,user_input,json_schema_input,json_function_name,json_function_description)
            print(assistant_answer)


    processes = Process.objects.all()

    process_perform_measure = ProcessPerformanceMeasurements.objects.all()

    qs = (
        ProcessPerformanceMeasurements.objects
        .annotate(month=TruncMonth('date'))
        .values('performance_indicator__name', 'month', 'measured_value', 'date')
        .order_by('performance_indicator__name', 'month', 'date')
    )

    months = sorted({row['month'] for row in qs})
    month_labels = [m.strftime('%Y-%m') for m in months]

    data = OrderedDict()
    for row in qs:
        name = row['performance_indicator__name']
        mon  = row['month'].strftime('%Y-%m')
        val  = float(row['measured_value'])

        if name not in data:
            data[name] = OrderedDict()

        data[name][mon] = val


    for series in data.values():
        for m in month_labels:
            series.setdefault(m, None)

    # 5) Prepara las listas para el gráfico
    kpi_labels = list(data.keys())
    kpi_series = [list(series.values()) for series in data.values()]


    context = {
        'processes': processes,
        'kpi_answer': assistant_answer,
        "selected_process_id": process_id,
        'process_perform_measure':process_perform_measure,
        'month_labels': month_labels,
        'kpi_labels'  : kpi_labels,
        'kpi_series'  : kpi_series,
        }

    return render(request, 'mistemplates/kpis-processes.html', context)
    

def process_risk_detector_ia(request):
    assistant_answer = None
    open_details_modal_id = None

    json_function_name = "risk_idetification_function"
    json_function_description = "This function should identify 2 or more risks and its consequencies in a process" \
                                "of a manufacturing plan according to ISO 9001:2015 norm and the given data."
    json_schema_input = {
    "type": "object",
    "properties": {
        "risks": {
            "type": "array",
            "description": "A list of identified risks with descriptions and consequences.",
            "items": {
                "type": "object",
                "properties": {
                    "risk": {
                        "type": "string",
                        "description": "Indicates a possible identified risk."
                    },
                    "risk_description": {
                        "type": "string",
                        "description": "Short description of the identified risk."
                    },
                    "consequence": {
                        "type": "string",
                        "description": "Consequence that the risk could have without explanation."
                    },
                    "consequence_description": {
                        "type": "string",
                        "description": "Short description of the consequence."
                    }
                },
                "required": [
                    "risk",
                    "risk_description",
                    "consequence",
                    "consequence_description"
                ],
                "additionalProperties": False
            },
        }
    },
    "required": ["risks"],
    "additionalProperties": False,
    "strict": False,
    "stream":True,
    }

    processes = Process.objects.all()

    if request.method == "POST":
        form_name = request.POST.get("form_name")

        if form_name == "process_risk_detector_form" :
            process_id = request.POST.get("process_id")

            process= Process.objects.get(id=process_id)
            activities = process.processactivity_set.all().order_by("order")
            activity_list = "\n".join([f"{a.order}. {a.activity}" for a in activities])

            process_data = f"""
                Estos son los datos del proceso:
                Nombre: {process.name}
                Objetivo: {process.objective}
                Pasos del proceso: {activity_list or "No especificados"}

                Espacios de trabajo: {process.workspaces or "No especificados"}
                Instalaciones: {process.facilities or "No especificadas"}
                Equipamiento: {process.equipment or "No especificado"}
                Materiales: {process.materials or "No especificados"}
                Recursos de transporte: {process.transport_resources or "No especificados"}
                Tecnologías de comunicación: {process.communication_technologies or "No especificadas"}
                Entorno operativo: {process.operational_environment or "No especificado"}

                Proveedores internos: {", ".join([a.name for a in process.internal_suppliers.all()]) or "Ninguno"}
                Proveedores externos: {", ".join([e.name for e in process.external_suppliers.all()]) or "Ninguno"}
                Clientes internos: {", ".join([a.name for a in process.internal_clients.all()]) or "Ninguno"}
                Clientes externos: {", ".join([e.name for e in process.external_clients.all()]) or "Ninguno"}

                Entradas del proceso: {", ".join([i.name for i in process.inputs.all()]) or "Ninguna"}
                Salidas del proceso: {", ".join([o.name for o in process.outputs.all()]) or "Ninguna"}
                Documentación: {", ".join([d.document_description for d in process.documents.all()]) or "Ninguna"}
                Indicadores de desempeño: {", ".join([i.name for i in process.performance_indicators.all()]) or "Ninguno"}
                """
            
            user_input = "Identify at least 3 specific risks and their potential consequences for the following process, focusing mainly on the provided process data. Use the ISO 9001:2015 standard only as a supporting framework to validate or guide your reasoning."\
                        "Your response must reflect the unique characteristics of the process and not rely on generic assumptions. Structure the result as a list of risks"

            assistant_answer = ai.ai_json_function(process_data,user_input,json_schema_input,json_function_name,json_function_description)

            print(assistant_answer)

            open_details_modal_id = f"riskModal{process_id}"

    context = {
        'processes': processes,
        'risk_answer': assistant_answer,
        'open_details_modal_id':open_details_modal_id
        }
    
    return render(request, 'mistemplates/processes.html',context)

    

def process_iso_compliance_ia(request):
    assistant_answer = None
    open_details_modal_id = None

    json_function_name = "iso_compliance_analizer_function"
    json_function_description = "Evaluate whether the following process complies with ISO 9001:2015. Identify specific aspects of the process that meet or align with the ISO 9001:2015 requirements and specific aspects that suggest potential non-compliance, gaps, or weaknesses according to the standard. There shoould be at least one of each."
    json_schema_input = {
        "type": "object",
        "properties": {
        "compliant_aspects": {
            "type": "array",
            "description": "Aspects of the process that are aligned with ISO 9001:2015",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "explanation": {"type": "string"}
                },
                "required": ["title", "explanation"],
                "additionalProperties": False
            }
        },
        "potential_noncompliances": {
            "type": "array",
            "description": "Aspects that may represent gaps or deviations from ISO 9001:2015",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "explanation": {"type": "string"}
                },
                "required": ["title", "explanation"],
                "additionalProperties": False
            }
        },
        "compliance_probability": {
                "type": "number",
                "minimum": 0,
                "maximum": 100,
                "description": "Estimated probability (as a percentage) that the process complies with ISO 9001:2015"
            }
        },
        "required": ["compliant_aspects", "potential_noncompliances", "compliance_probability"],
        "additionalProperties": False
    }

    processes = Process.objects.all()

    if request.method == "POST":
        form_name = request.POST.get("form_name")

        if form_name == "process_iso_compliance_form" :
            process_id = request.POST.get("process_id")

            process= Process.objects.get(id=process_id)
            activities = process.processactivity_set.all().order_by("order")
            activity_list = "\n".join([f"{a.order}. {a.activity}" for a in activities])

            process_data = f"""
                Estos son los datos del proceso:
                Nombre: {process.name} \\
                Objetivo: {process.objective}
                Pasos del proceso: {activity_list or "No especificados"}

                Espacios de trabajo: {process.workspaces or "No especificados"}
                Instalaciones: {process.facilities or "No especificadas"}
                Equipamiento: {process.equipment or "No especificado"}
                Materiales: {process.materials or "No especificados"}
                Recursos de transporte: {process.transport_resources or "No especificados"}
                Tecnologías de comunicación: {process.communication_technologies or "No especificadas"}
                Entorno operativo: {process.operational_environment or "No especificado"}

                Proveedores internos: {", ".join([a.name for a in process.internal_suppliers.all()]) or "Ninguno"}
                Proveedores externos: {", ".join([e.name for e in process.external_suppliers.all()]) or "Ninguno"}
                Clientes internos: {", ".join([a.name for a in process.internal_clients.all()]) or "Ninguno"}
                Clientes externos: {", ".join([e.name for e in process.external_clients.all()]) or "Ninguno"}

                Entradas del proceso: {", ".join([i.name for i in process.inputs.all()]) or "Ninguna"}
                Salidas del proceso: {", ".join([o.name for o in process.outputs.all()]) or "Ninguna"}
                Documentación: {", ".join([d.document_description for d in process.documents.all()]) or "Ninguna"}
                Indicadores de desempeño: {", ".join([i.name for i in process.performance_indicators.all()]) or "Ninguno"}
                """
            
            user_input = "Evaluate whether the following process complies with ISO 9001:2015. Use the provided process data to identify.Your response must reflect the actual content of the process data. Avoid generic or fabricated insights. Do not leave either section empty."

            assistant_answer = ai.ai_json_function(process_data,user_input,json_schema_input,json_function_name,json_function_description)

            open_details_modal_id = f"complianceModal{process_id}"

            print(assistant_answer )

    context = {
        'processes': processes,
        'analysis_answer' : assistant_answer,
        'open_details_modal_id':open_details_modal_id
        }
    
    return render(request, 'mistemplates/processes.html',context)


def process_summarize_ia(request):
    assistant_answer = None
    open_details_modal_id = None
    max_tokens= 50

    processes = Process.objects.all()

    if request.method == "POST":
        form_name = request.POST.get("form_name")

        if form_name == "process_summarize_form" :
            process_id = request.POST.get("process_id")

            process= Process.objects.get(id=process_id)
            activities = process.processactivity_set.all().order_by("order")
            activity_list = "\n".join([f"{a.order}. {a.activity}" for a in activities])

            process_data = f"""
                Estos son los datos del proceso:
                Nombre: {process.name} \\
                Objetivo: {process.objective}
                Pasos del proceso: {activity_list or "No especificados"}

                Espacios de trabajo: {process.workspaces or "No especificados"}
                Instalaciones: {process.facilities or "No especificadas"}
                Equipamiento: {process.equipment or "No especificado"}
                Materiales: {process.materials or "No especificados"}
                Recursos de transporte: {process.transport_resources or "No especificados"}
                Tecnologías de comunicación: {process.communication_technologies or "No especificadas"}
                Entorno operativo: {process.operational_environment or "No especificado"}

                Proveedores internos: {", ".join([a.name for a in process.internal_suppliers.all()]) or "Ninguno"}
                Proveedores externos: {", ".join([e.name for e in process.external_suppliers.all()]) or "Ninguno"}
                Clientes internos: {", ".join([a.name for a in process.internal_clients.all()]) or "Ninguno"}
                Clientes externos: {", ".join([e.name for e in process.external_clients.all()]) or "Ninguno"}

                Entradas del proceso: {", ".join([i.name for i in process.inputs.all()]) or "Ninguna"}
                Salidas del proceso: {", ".join([o.name for o in process.outputs.all()]) or "Ninguna"}
                Documentación: {", ".join([d.document_description for d in process.documents.all()]) or "Ninguna"}
                Indicadores de desempeño: {", ".join([i.name for i in process.performance_indicators.all()]) or "Ninguno"}
                """
            
            user_input = "Summarize this process of a manufacturing company in less than 1000 characters. Your response must reflect the actual content of the process data. Avoid generic or fabricated insights."

            assistant_answer = ai.ai_text_function(process_data,user_input,max_tokens)

            open_details_modal_id = f"summarizeModal{process_id}"

            print(assistant_answer)

    context = {
        'processes': processes,
        'process_summary' : assistant_answer,
        'open_details_modal_id':open_details_modal_id
        }
    
    return render(request, 'mistemplates/processes.html',context)


def checklist_detector_ia(request):

    return render(request, 'mistemplates/processes.html')