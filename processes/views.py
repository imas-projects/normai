'''
from django.shortcuts import render, redirect, get_object_or_404
from .models import Process
from django.contrib.auth.models import User
from .forms import ProcessForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Process, PositionRole, Supplier, ProcessInput, PerformanceIndicator, ProcessMeasurement, ProcessOutput, JobPosition, Client, Resource, Documentation, Activity
from django.http import JsonResponse
import json
import datetime

def list_processes(request):
    processes = Process.objects.select_related('responsible').prefetch_related(
        'positions', 'suppliers', 'inputs', 'outputs',
        'clients', 'activities', 'resources', 'documents',
        'measurements', 'indicators').all()

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
    positions_options = list(PositionRole.objects.select_related('position').values('id', 'role', 'position__name'))
    suppliers_options = list(Supplier.objects.all().values('id', 'name'))
    inputs_options= list(ProcessInput.objects.all().values('id', 'description'))
    outputs_options= list(ProcessOutput.objects.all().values('id', 'description'))
    activities_options= list(Activity.objects.all().values('id', 'description','order'))
    resources_options= list(Resource.objects.all().values('id', 'description'))
    documents_options= list(Documentation.objects.all().values('id', 'description','documentation_code','type'))
    measurements_options= list(ProcessMeasurement.objects.all().values('id', 'description','measurement_type'))
    indicators_options= list(PerformanceIndicator.objects.all().values('id', 'name'))
    clients_options=list(Client.objects.all().values('id', 'name'))

    return {
        'responsible_options' : responsible_options,
        'positions_options' : positions_options,
        'suppliers_options' : suppliers_options,
        'inputs_options' : inputs_options,
        'outputs_options' : outputs_options,
        'activities_options' : activities_options,
        'documents_options' : documents_options,
        'indicators_options' : indicators_options,
        'activities_options' : activities_options,
        'resources_options' : resources_options,
        'measurements_options' : measurements_options,
        'clients_options' : clients_options,

    }

def get_process(request, id):
    try:
        current_process = Process.objects.get(id=id)

        current_process_positions= list(current_process.positions.all().values('id', 'role','position'))
        current_process_suppliers = list(current_process.suppliers.all().values('id', 'name', 'type'))
        current_process_clients = list(current_process.clients.all().values('id', 'name', 'type'))
        current_process_inputs = list(current_process.inputs.all().values('id', 'description'))
        current_process_outputs = list(current_process.outputs.all().values('id', 'description'))
        current_process_activities = list(current_process.activities.all().values('id', 'description','order'))
        current_process_resources = list(current_process.resources.all().values('id', 'description'))
        current_process_documents = list(current_process.documents.all().values('id', 'description','documentation_code','type'))
        current_process_measurements = list(current_process.measurements.all().values('id', 'description','measurement_type'))
        current_process_indicators = list(current_process.indicators.all().values('id', 'name'))

        form_options = load_form_options()

        return JsonResponse({
            'success': True, 
            # Campos unicos o foreign key
            'id': current_process.id,
            'name' : current_process.name,
            'objective': current_process.objective,
            'responsible': current_process.responsible.id,

            # Campos manytomany
            'positions': current_process_positions,
            'suppliers': current_process_suppliers,
            'clients' : current_process_clients,
            'inputs' : current_process_inputs,
            'outputs' : current_process_outputs,
            'activities': current_process_activities,
            'resources' : current_process_resources,
            'documents': current_process_documents,
            'measurements' : current_process_measurements,
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
                selected_positions = data.get('process_positions', [])  # Many-to-Many
                selected_suppliers = data.get('process_suppliers', [])  # Many-to-Many
                selected_inputs = data.get('process_inputs', [])
                selected_outputs = data.get('process_outputs', [])
                selected_clients = data.get('process_clients', [])
                selected_activities = data.get('process_activities', [])
                selected_resources = data.get('process_resources', [])
                selected_documents = data.get('process_documents', [])
                selected_measurements = data.get('process_measurements', [])
                selected_indicators = data.get('process_indicators', [])

                updated_process = Process.objects.get(id=process_id)
                updated_process.name = process_name
                updated_process.objective = process_objective
                updated_process.review_date = process_review_date

                updated_process.responsible = User.objects.get(id=process_responsible) 

                updated_process.positions.set(selected_positions)
                updated_process.positions.set(selected_positions)
                updated_process.suppliers.set(selected_suppliers)
                updated_process.inputs.set(selected_inputs)
                updated_process.outputs.set(selected_outputs)
                updated_process.clients.set(selected_clients)
                updated_process.activities.set(selected_activities)
                updated_process.resources.set(selected_resources)
                updated_process.documents.set(selected_documents)
                updated_process.measurements.set(selected_measurements)
                updated_process.indicators.set(selected_indicators)


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

'''