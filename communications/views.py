from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import CommunicationTable, CommunicationType, Message, Channel, Periodicity, CommunicationMessage, MessageChanel
from company.models import Area
from django.contrib.auth.models import Group, User
from django.http import JsonResponse
import json


# Create your views here.

# Funciones para chequear permisos
# Prueba acceso a all_messages solo si pertenece al grupo "comunicaciones" (Funciona)
'''
def communication_check(user):
    check_communication_group = user.groups.filter(name="comunicaciones").exists()
    if check_communication_group is True:
        print(user.groups.all())
        return (check_communication_group)
    else:
        raise PermissionDenied 
'''
# Carga la información de todos los mensajes. Requiere login y tener permisos
@csrf_protect
@login_required
#@user_passes_test(communication_check)

def all_messages(request):
    #user_in_comunicadores = request.user.groups.filter(name="comunicadores").exists()

    all_communicationtables = CommunicationTable.objects.prefetch_related(
    'message__type',
    'message__receiver',
    'message__periodicity',
    )

    context = {
        'all_communicationtables': all_communicationtables,

    }

    return render(request, "mistemplates/communication-tables.html", context)
    



# Esta función recoge las informacion de las tablas relacionadas con los mensajes.
# Se usa para cargar los campos de un mensaje o las opciones seleccionables de los formularios de editar/añadir mensaje.
# Evita tener que repetir estas mismas líneas en las otras dos funciones.
def load_form_options():
    all_periodicities = list(Periodicity.objects.all().values('id', 'name')) 
    all_communicationtypes = list(CommunicationType.objects.all().values('id', 'scope', 'direction')) 
    all_departments = list(User.objects.all().values('id', 'first_name','last_name','groups'))
    all_channels = list(Channel.objects.all().values('id','name'))

    return {
        'periodicity_options' : all_periodicities,
        'communicationtype_options' : all_communicationtypes,
        'departments_options' : all_departments,
        'channels_options' : all_channels
    }



# Función para obtener la info del mensaje en el que hemos dado a editar y rellenar el formulario de edición.
def get_message(request, id):
    try:
        current_message = Message.objects.get(id=id)

        # Lista de los datos en los campos que pueden contener varios valores
        current_message_channels = list(current_message.channels.all().values('id', 'name'))
        current_message_receivers = list(current_message.receivers.all().values('id', 'first_name','last_name'))

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
@csrf_protect
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
            updated_message.transmitter = User.objects.get(id=message_transmitter) 
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
@csrf_protect
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

def load_messageform_options_asJson(request):
    try:
        form_options = load_form_options()
        return JsonResponse({
            'success' : True,
            **form_options, 
            })
    except CommunicationTable.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Row not found.'})

@login_required
def load_addtableform_options_asJson(request):
    all_emiter= list(User.objects.all().values('id', 'first_name','last_name'))
    all_areas = list(Area.objects.all().values('id','name'))
    # print(all_areas)
    #'departments_options' : all_departments,
    try:
        return JsonResponse({
                'success' : True,
                'emiter_options' : all_emiter, 
                'areas_options' : all_areas,
                })
    except:
        return JsonResponse({'success': False, 'error': 'Error'})

@csrf_protect
def create_message(request):
    if request.method == 'POST':
        try:
            # Coger los valores introducidos en el formulario
            data = json.loads(request.body)
            communication_table_id = data.get('communication_table_id')
            message_communication_type = data.get('message_communication_type')  # Foreign key
            message_subject = data.get('message_subject')  # Simple text field
            message_periodicity = data.get('message_periodicity')  # Foreign key
            selected_channels = data.get('message_channels', [])  # Many-to-Many
            message_receiver = data.get('message_receivers')  # Un receptor por mensaje
            
            # Crear el nuevo mensaje
            message = Message.objects.create(name=message_subject)
            
             # Crear relaciones MessageChannel
            for channel_id in selected_channels:
                MessageChanel.objects.create(
                    message_id=message.id,
                    channel_id=channel_id
            )
            
            # Crear relaciones CommunicationMessage (una por receptor)
            CommunicationMessage.objects.create(
                type_id=message_communication_type,
                table_id=communication_table_id,
                message_id=message.id,
                receiver_id=message_receiver,
                periodicity_id=message_periodicity
            )
            print('ok')

            return JsonResponse({'success': True})
        except Message.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Row not found.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

import datetime

@csrf_protect
@login_required
def create_table(request):
    user = request.user
    
    if request.method == 'POST':
        try:
            # Coger los valores introducidos en el formulario
            data = json.loads(request.body) 
            table_code = data.get('table_code')  # Simple text field
            table_emiter = data.get('table_emiter')  # Foreign key
            table_area = data.get('table_area')
            table_creator = data.get('table_creator')
            
            # Crear tabla
            new_table = CommunicationTable(
                code=table_code,
                emiter=User.objects.get(id=table_emiter),
                review_date=datetime.date.today(),
                review_number=0,
                area=Area.objects.get(id=table_area),
                created_by=User.objects.get(id=table_creator)
                )
            # Guardar tabla
            new_table.save()  

            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

@csrf_protect
@login_required
#@user_passes_test(communication_check)
def user_received_messages(request):
    user = request.user
    user_areas = Area.objects.filter(users=user)

    all_communicationtable = CommunicationTable.objects.filter(area__in=user_areas).distinct()
    all_communicationtables = list(all_communicationtable)


    all_messages = Message.objects.filter(receivers=user).distinct()
    all_messages = [message for message in all_messages]

    # Contexto para la plantilla
    context = {
        'all_messages' : all_messages,
        'all_communicationtables': all_communicationtables
    }
    return render(request,"mistemplates/user-received-messages.html", context)


@csrf_protect
@login_required
#@user_passes_test(communication_check)
def user_sent_messages(request):
    user = request.user
    user_areas = Area.objects.filter(users=user)

    all_communicationtable = CommunicationTable.objects.filter(area__in=user_areas).distinct()
    all_communicationtables = list(all_communicationtable)


    all_messages = Message.objects.filter(transmitter=user).distinct()
    all_messages = [message for message in all_messages]

    # Contexto para la plantilla
    context = {
        'all_messages' : all_messages,
        'all_communicationtables': all_communicationtables
    }
    return render(request,"mistemplates/user-sent-messages.html", context)


@csrf_protect
@login_required
#@user_passes_test(communication_check)
def communication_table_review(request):
    user = request.user
    #user_area = Area.objects.get(users=user)
    user_areas = Area.objects.filter(users=user)

    all_communicationtable = CommunicationTable.objects.filter(area__in=user_areas).distinct()
    all_communicationtables = list(all_communicationtable)

    all_messages = Message.objects.filter(transmitter=user).distinct()
    all_messages = [message for message in all_messages]

    all_status = list(CommunicationTable.STATUS_CHOICES)

    context = {
        'all_messages' : all_messages,
        'all_communicationtables': all_communicationtables,
        'all_status' : all_status,
    }

    if request.method == "POST":
        try:
            data = json.loads(request.body)
            table_id = data.get("table_id")
            new_status = data.get("status")
            
            table = get_object_or_404(CommunicationTable, id=table_id)
            table.status = new_status
            
            if new_status == "approved":
                table.approved_by = request.user  # Asignar el usuario autenticado como revisor
                table.save()

            else:
                table.reviewed_by = request.user  # Asignar el usuario autenticado como revisor
                table.save()
            
            return JsonResponse({"success": True, "message": "Tabla actualizada correctamente"})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    
    #return JsonResponse({"success": False, "error": "Error al actualizar la tabla"})

    return render(request,"mistemplates/communication-tables-review.html", context)

