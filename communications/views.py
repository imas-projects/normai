from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import CommunicationTable, CommunicationType, Message, Channel, Periodicity
from risks.models import Department
from django.http import JsonResponse
import json


# Create your views here.
'''
class DashboardView(LoginRequiredMixin,TemplateView): #Quito esto para no tener que hacer login
'''
######################## TABLAS DE COMUNICACIONES ########################

# Carga la información de todas las Tablas de Comunicaciones
def communication_table_view(request):
    all_communicationtable = CommunicationTable.objects.all()  # Get all entries
    communicationtable_info = [table.as_dict() for table in all_communicationtable]

    return render(request,"mistemplates/communication-tables.html",{'communicationtable_info':communicationtable_info})


# Carga la información de todos los mensajes.
@login_required
def all_messages(request):
    #user_in_comunicadores = request.user.groups.filter(name="comunicadores").exists()

    all_communicationtable = CommunicationTable.objects.all()  # Get all entries
    all_communicationtables = [table.as_dict() for table in all_communicationtable]
    
    all_messages = Message.objects.all()
    message = [message.as_dict() for message in all_messages]

    all_channels = Channel.objects.all()
    all_channels = [channel.as_dict() for channel in all_channels]

    context ={
        'messages' : message,
        'all_communicationtables' : all_communicationtables,
        'all_channels' : all_channels,
        #'user_in_comunicadores': user_in_comunicadores
    }
    return render(request,"mistemplates/communication-tables.html",context)



# Esta función recoge las informacion de las tablas relacionadas con los mensajes.
# Se usa para cargar los campos de un mensaje o las opciones seleccionables de los formularios de editar/añadir mensaje.
# Evita tener que repetir estas mismas líneas en las otras dos funciones.
def load_form_options():
    all_periodicities = list(Periodicity.objects.all().values('id', 'name')) 
    all_communicationtypes = list(CommunicationType.objects.all().values('id', 'scope', 'direction')) 
    all_departments = list(Department.objects.all().values('id', 'name'))
    all_channels = list(Channel.objects.all().values('id','name'))

    return {
        'periodicity_options' : all_periodicities,
        'communicationtype_options' : all_communicationtypes,
        'departments_options' : all_departments,
        'channels_options' : all_channels,
    }



# Función para obtener la info del mensaje en el que hemos dado a editar y rellenar el formulario de edición.
def get_message(request, id):
    try:
        current_message = Message.objects.get(id=id)

        # Lista de los datos en los campos que pueden contener varios valores
        current_message_channels = list(current_message.channels.all().values('id', 'name'))
        current_message_receivers = list(current_message.receivers.all().values('id', 'name'))

        # Cargar el resto de tablas
        form_options = load_form_options()

        return JsonResponse({
            'success': True, 
            # Campos unicos o foreign key
            'id': current_message.id,
            'communication_type' : current_message.communication_type.id,
            'subject': current_message.subject,
            'transmitter': current_message.transmitter.id,
            'periodicity': current_message.periodicity.id,

            # Campos manytomany
            'channels': current_message_channels,
            'receivers': current_message_receivers,

            # Opciones formulario
            **form_options,
        })
    except Message.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Row not found.'})
    

# Aplicación de las modificaciones hechas en un mensaje
@csrf_exempt
def update_message(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            message_id = data.get('id')
            message_communication_type = data.get('message_communication_type')  # Foreign key
            message_subject = data.get('message_subject')  # Simple text field
            message_transmitter = data.get('message_transmitter')  # Foreign key
            message_periodicity = data.get('message_periodicity')  # Foreign key
            selected_channels = data.get('message_channel', [])  # Many-to-Many
            selected_receivers = data.get('message_receiver', [])  # Many-to-Many
            print("mensaje", data)
            # Get the message object
            updated_message = Message.objects.get(id=message_id)

            # Update foreign key fields
            updated_message.communication_type = CommunicationType.objects.get(id=message_communication_type)  # Assign directly to FK field
            updated_message.transmitter = Department.objects.get(id=message_transmitter) 
            updated_message.periodicity = Periodicity.objects.get(id=message_periodicity) 
            
            # Update simple fields
            updated_message.subject = message_subject

            # Update Many-to-Many fields
            updated_message.channels.set(selected_channels)  # Set new channels
            updated_message.receivers.set(selected_receivers)  # Set new receivers

            # Save the changes
            updated_message.save()

            return JsonResponse({'success': True})
        except Message.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Row not found.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})


# Eliminación de mensaje de la tabla
@csrf_exempt
def delete_message(request, id):
    if request.method == 'POST':
        try:
            # Buscar y eliminar el mensaje
            deleted_message = Message.objects.get(id=id)
            deleted_message.delete()
            return JsonResponse({'success': True})
        except Message.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Message not found'})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


# Añadir Mensaje
@csrf_exempt
def load_messageform_options_asJson(request):
    try:
        form_options = load_form_options()
        return JsonResponse({
            'success' : True,
            **form_options, 
            })
    except CommunicationTable.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Row not found.'})

def load_addtableform_options_asJson(request):
    all_departments = list(Department.objects.all().values('id', 'name'))
    #'departments_options' : all_departments,
    try:
        return JsonResponse({
                'success' : True,
                'departments_options' : all_departments, 
                })
    except:
        return JsonResponse({'success': False, 'error': 'Error'})


def create_message(request):
    if request.method == 'POST':
        try:
            # Coger los valores introducidos en el formulario
            data = json.loads(request.body)
            communication_table_id = data.get('communication_table_id')
            message_communication_type = data.get('message_communication_type')  # Foreign key
            message_subject = data.get('message_subject')  # Simple text field
            message_transmitter = data.get('message_transmitter')  # Foreign key
            message_periodicity = data.get('message_periodicity')  # Foreign key
            selected_channels = data.get('message_channels', [])  # Many-to-Many
            selected_receivers = data.get('message_receivers', [])  # Many-to-Many
            
            # Crear el nuevo mensaje
            new_message = Message(
                communication_type=CommunicationType.objects.get(id=message_communication_type),
                subject=message_subject,
                transmitter=Department.objects.get(id=message_transmitter),
                periodicity=Periodicity.objects.get(id=message_periodicity),
                )
            
            # Hay que guardar el mensaje antes de asignarle los campos many-to-many y la tabla a la que pertenece
            new_message.save()

            # Campos many-to-many
            new_message.channels.set(selected_channels)
            new_message.receivers.set(selected_receivers)

            # Se mete el nuevo mensaje en la tabla correspondiente    
            table_new_message = CommunicationTable.objects.get(id=communication_table_id)
            table_new_message.messages.add(new_message)


            return JsonResponse({'success': True})
        except Message.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Row not found.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

import datetime

def create_table(request):
    if request.method == 'POST':
        try:
            # Coger los valores introducidos en el formulario
            data = json.loads(request.body) 
            table_code = data.get('table_code')  # Simple text field
            table_transmitter = data.get('table_transmitter')  # Foreign key
            
            # Crear tabla
            new_table = CommunicationTable(
                code=table_code,
                created_by=Department.objects.get(id=table_transmitter),
                review_date=datetime.date.today(),
                review_number=0,
                reviewed_by=Department.objects.get(id=0),
                approved_by=Department.objects.get(id=0),
                )
            # Guardar tabla
            new_table.save()  

            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})
