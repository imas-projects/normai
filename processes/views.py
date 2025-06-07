from django.shortcuts import render, redirect, get_object_or_404
from .models import Process
from django.contrib.auth.models import User
from .forms import ProcessForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Process, ProcessInput, PerformanceIndicator, ProcessMeasurement, ProcessOutput, Documentation, ProcessActivity, ProcessPosition, ProductMeasurement
from company.models import ExternalClient, ExternalSupplier, Area, Position
from django.http import JsonResponse
import json
import datetime

def list_processes(request):
    processes = Process.objects.all()

    return render(request, 'mistemplates/processes.html', {'processes': processes})


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


def load_form_options():
    responsible_options = list(User.objects.all().values('id', 'first_name', 'last_name'))
    internal_suppliers_options = list(Area.objects.all().values('id', 'name'))
    external_suppliers_options = list(ExternalSupplier.objects.all().values('id', 'name'))
    internal_clients_options = list(Area.objects.all().values('id', 'name'))
    external_clients_options = list(ExternalClient.objects.all().values('id', 'name'))
    inputs_options= list(ProcessInput.objects.all().values('id', 'name'))
    outputs_options= list(ProcessOutput.objects.all().values('id', 'name'))
    documents_options= list(Documentation.objects.all().values('id', 'document_description','document_code'))
    measurements_options= list(ProcessMeasurement.objects.all().values('id','measurement_process_parameter'))
    indicators_options= list(PerformanceIndicator.objects.all().values('id', 'name'))

    return {
        'responsible_options' : responsible_options,
        'internal_suppliers_options' : internal_suppliers_options,
        'external_suppliers_options' : external_suppliers_options,
        'internal_clients_options' : internal_clients_options,
        'external_clients_options' : external_clients_options,
        'inputs_options' : inputs_options,
        'outputs_options' : outputs_options,
        'documents_options' : documents_options,
        'indicators_options' : indicators_options,
        'measurements_options' : measurements_options,
    }

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
        current_process_indicators = list(current_process.performance_indicators.all().values('id', 'name'))

        form_options = load_form_options()

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
            'indicators' : current_process_indicators,

            # Opciones formulario
            **form_options,
        })
    except Process.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Row not found.'})

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

                selected_internal_suppliers = data.get('process_internal_suppliers', []) 
                selected_external_suppliers = data.get('process_external_suppliers', [])  
                selected_inputs = data.get('process_inputs', [])
                selected_outputs = data.get('process_outputs', [])
                selected_internal_clients = data.get('process_internal_clients', [])
                selected_external_clients = data.get('process_external_clients', [])
                selected_documents = data.get('process_documents', [])
                selected_indicators = data.get('process_indicators', [])

                updated_process = Process.objects.get(id=process_id)
                updated_process.name = process_name
                updated_process.objective = process_objective
                updated_process.review_date = process_review_date
                updated_process.responsible = User.objects.get(id=process_responsible) 

                updated_process.inputs.set(selected_inputs)
                updated_process.outputs.set(selected_outputs)
                updated_process.internal_clients.set(selected_internal_clients)
                updated_process.external_clients.set(selected_external_clients)
                updated_process.internal_suppliers.set(selected_internal_suppliers)
                updated_process.external_suppliers.set(selected_external_suppliers)
                updated_process.documents.set(selected_documents)
                updated_process.performance_indicators.set(selected_indicators)


                updated_process.save()
                return JsonResponse({'success': True})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid method'})

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


############## Views con IA
from ai_functions import implementation_functions as ai

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

            open_details_modal_id = f"detailsModal{process_id}"

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
            
            user_input = "Evaluate whether the following process complies with ISO 9001:2015. Use the provided process data to identify.Your response must reflect the actual content of the process data. Avoid generic or fabricated insights. Do not leave either section empty."

            assistant_answer = ai.ai_json_function(process_data,user_input,json_schema_input,json_function_name,json_function_description)

            open_details_modal_id = f"detailsModal{process_id}"

            print(assistant_answer )

    context = {
        'processes': processes,
        'analysis_answer' : assistant_answer,
        'open_details_modal_id':open_details_modal_id
        }
    
    return render(request, 'mistemplates/processes.html',context)


def process_flow_diagram_ia(request):
    assistant_answer = None
    open_details_modal_id = None

    json_function_name = "process_flow_diagram_generator"
    json_function_description = "Creates a flow diagram of a process according to its activities. If necessary, add connections and additional important considerations."
    json_schema_input = {
        "type": "object",
        "properties": {
            "flow": {
                "type": "array",
                "description": "Each of the steps of the process including its order, title and possible connextions or other considerations.",
                "items": {
                    "type": "object",
                    "properties": {
                        "order": {"type": "integer"},
                        "title": {"type": "string"},
                        "connections": {"type": "string"},
                        "additional_considerations": {"type": "string"}
                    },
                    "required": [
                        "order", 
                        "title", 
                        "connections", 
                        "additional_considerations"
                    ],
                    "additionalProperties": False
                }
            }
        },
        "required": ["flow"],
        "additionalProperties": False
    }

    processes = Process.objects.all()

    if request.method == "POST":
        form_name = request.POST.get("form_name")

        if form_name == "process_flow_diagram_form" :
            process_id = request.POST.get("process_id")

            process= Process.objects.get(id=process_id)
            activities = process.processactivity_set.all().order_by("order")
            activity_list = "\n".join([f"{a.order}. {a.activity}" for a in activities])

            process_data = f"""
                Nombre: {process.name}
                Objetivo: {process.objective}
                Pasos del proceso: {activity_list or "No especificados"}

                Entradas del proceso: {", ".join([i.name for i in process.inputs.all()]) or "Ninguna"}
                Salidas del proceso: {", ".join([o.name for o in process.outputs.all()]) or "Ninguna"}
                """
            
            user_input = "Your response must reflect the actual content of the process data. Avoid generic or fabricated insights."

            assistant_answer = ai.ai_json_function(process_data,user_input,json_schema_input,json_function_name,json_function_description)

            open_details_modal_id = f"detailsModal{process_id}"

            print(assistant_answer)

    context = {
        'processes': processes,
        'process_flow_answer' : assistant_answer,
        'open_details_modal_id':open_details_modal_id
        }
    
    return render(request, 'mistemplates/processes.html',context)
