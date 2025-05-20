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

                updated_process.staff_roles.set(process_staff_roles)
                updated_process.workspaces.set(process_workspaces)
                updated_process.facilities.set(process_facilities)
                updated_process.equipment.set(process_equipment)
                updated_process.materials.set(process_materials)
                updated_process.transport_resources.set(process_transport_resources)
                updated_process.communication_technologies.set(process_communication_technologies)
                updated_process.operational_environment.set(process_operational_environment)


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
