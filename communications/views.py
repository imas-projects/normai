from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import CommunicationTable, CommunicationType, Message, Channel, Periodicity, CommunicationMessage, MessageChanel
from company.models import Area, Position, UserPosition
from django.contrib.auth.models import Group, User
from django.http import JsonResponse
import json
from ai_functions.monitoring_functions import generate_communication_flow_map


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
    'message__message__message_channels__channel'
    )


    # -- Gráficas
    datos_comunicaciones = (
        CommunicationMessage.objects
        .values('table__emiter__id', 'table__emiter__name','table__emiter__area') 
        .annotate(total=Count('id'))
        .order_by('-total')
    )

    areas_emiters = [item['table__emiter__area'] for item in datos_comunicaciones]

    communication_areas=[]
    for a in areas_emiters:
        cm=Area.objects.get(id=a)
        communication_areas.append(cm.name)
    
        
    #communications_labels=[item['table__emiter__name'] for item in datos_comunicaciones]
    communications_labels=communication_areas
    communications_values=[item['total'] for item in datos_comunicaciones]

    # -- últimas comunicaciones
    mensajes = (
        CommunicationMessage.objects
        .select_related('message', 'table', 'receiver', 'table__emiter')
        .order_by('-id')[:5]
    )

    resultados = []
    for m in mensajes:
        resultados.append({
            'asunto': m.message.name,
            'emisor': m.table.emiter.name if m.table and m.table.emiter else "Sin emisor",
            'receptor': m.receiver.name if m.receiver else "Sin receptor",
        })

    emisores_recientes = [r['emisor'] for r in resultados]
    receptores_recientes = [r['receptor'] for r in resultados]
    asuntos_recientes = [r['asunto'] for r in resultados]
    comunicaciones_recientes = resultados


    context = {
        'all_communicationtables': all_communicationtables,
        'communications_labels':communications_labels,
        'communications_values':communications_values,
        'emisores_recientes':emisores_recientes,
        'receptores_recientes':receptores_recientes,
        'asuntos_recientes':asuntos_recientes,
        'comunicaciones_recientes':comunicaciones_recientes

    }

    return render(request, "mistemplates/communication-tables.html", context)
    

# Esta función recoge las informacion de las tablas relacionadas con los mensajes.
# Se usa para cargar los campos de un mensaje o las opciones seleccionables de los formularios de editar/añadir mensaje.
# Evita tener que repetir estas mismas líneas en las otras dos funciones.
def load_form_options():
    all_periodicities = list(Periodicity.objects.all().values('id', 'name')) 
    all_communicationtypes = list(CommunicationType.objects.all().values('id', 'scope', 'direction')) 
    all_departments = list(Position.objects.all().values('id', 'name'))
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
        current_message_info = CommunicationMessage.objects.select_related("message", "type", "receiver", "periodicity").get(id=id)

        message = current_message_info.message

        message_channel = MessageChanel.objects.filter(message=message)

        form_options = load_form_options()

        return JsonResponse({
            'success': True,
            'id': current_message_info.id,  # id del CommunicationMessage
            'communication_type': current_message_info.type.id,
            'subject': message.name,
            'periodicity': current_message_info.periodicity.id,
            'receivers': current_message_info.receiver.id,
            'channels': [msg.channel.id for msg in message_channel],
            **form_options,
        })
    except Message.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Row not found.'})
    

# Aplicación de las modificaciones hechas en un mensaje
@csrf_protect
@login_required
def update_message(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            com_message_id = data.get('id')  # CommunicationMessage ID
            communication_type_id = data.get('message_communication_type')
            subject = data.get('message_subject')
            periodicity_id = data.get('message_periodicity')
            channel_id = [data.get('message_channel')]
            receiver_id = data.get('message_receiver')

            # Obtener el CommunicationMessage y su Message relacionado
            com_message = CommunicationMessage.objects.get(id=com_message_id)
            message = com_message.message

            # Actualizar campos
            message.name = subject
            com_message.type_id = communication_type_id
            com_message.periodicity_id = periodicity_id
            com_message.receiver_id = receiver_id

            # Actualizar canal
            MessageChanel.objects.filter(message=message).delete()

            # Crear nuevos canales
            for channel_id in channel_id:
                MessageChanel.objects.create(message=message, channel_id=channel_id)

            # Guardar cambios
            message.save()
            com_message.save()
            


            return JsonResponse({'success': True})
        except Message.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Row not found.'})
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})


# Eliminación de mensaje de la tabla
@csrf_protect
@login_required
def delete_message(request, id):
    if request.method == 'POST':
        try:
            message = Message.objects.get(id=id)
            MessageChanel.objects.filter(message=message).delete()
            CommunicationMessage.objects.filter(message=message).delete()
            message.delete()
            return JsonResponse({'success': True})
        except Message.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Message not found'})
        except Exception as e:
            import traceback
            traceback.print_exc()
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
    all_emiter= list(Position.objects.all().values('id', 'name'))
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
@login_required
def create_message(request):
    if request.method == 'POST':
        try:
            # Coger los valores introducidos en el formulario
            data = json.loads(request.body)
            communication_table_id = data.get('communication_table_id')
            message_communication_type = data.get('message_communication_type')  # Foreign key
            message_subject = data.get('message_subject')  # Simple text field
            message_periodicity = data.get('message_periodicity')  # Foreign key
            selected_channels = data.get('message_channels')  # Many-to-Many
            message_receiver = data.get('message_receivers')  # Un receptor por mensaje
            
            # Crear el nuevo mensaje
            message = Message.objects.create(name=message_subject)
            message.save()
            

             # Crear relaciones MessageChannel
            message_channel = MessageChanel.objects.create(
                message_id=message.id,
                channel_id=selected_channels,
                table_id = communication_table_id
            )
            message_channel.save()
            
            # Crear relaciones CommunicationMessage (una por receptor)
            com_message = CommunicationMessage.objects.create(
                type_id=message_communication_type,
                table_id=communication_table_id,
                message_id=message.id,
                receiver_id=message_receiver,
                periodicity_id=message_periodicity
            )
            com_message.save()


            return JsonResponse({'success': True})
        except Message.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Row not found.'})
        except Exception as e:
            import traceback
            traceback.print_exc()
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
            #table_area = data.get('table_area')
            table_creator = data.get('table_creator')

           # table_emiter_position = UserPosition.objects.get(user_id=table_emiter)

            table_creator_position = UserPosition.objects.get(user_id=table_creator)
            
            # Crear tabla
            new_table = CommunicationTable(
                code=table_code,
                emiter=Position.objects.get(id=table_emiter),
                review_date=datetime.date.today(),
                review_number=0,
                #area=Area.objects.get(id=table_area),
                created_by=Position.objects.get(id=table_creator_position.position_id)
                )
            # Guardar tabla
            new_table.save()  

            return JsonResponse({'success': True})
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

@csrf_protect
@login_required
#@user_passes_test(communication_check)
def user_received_sent_messages(request):
    user = request.user
    user_position = UserPosition.objects.get(user_id=user)

    received_messages = CommunicationMessage.objects.filter(receiver=user_position.position).distinct()
    received_messages = [message for message in received_messages]

    sent_messages_table = CommunicationTable.objects.filter(emiter=user_position.position)
    sent_messages = CommunicationMessage.objects.filter(table__in=sent_messages_table)

    comunicaciones_labels = ['Recibidas','Enviadas']
    comunicaciones_values = [len(received_messages),len(sent_messages)]
  

    # Contexto para la plantilla
    context = {
        'received_messages' : received_messages,
        'sent_messages' : sent_messages,
        'comunicaciones_labels':comunicaciones_labels,
        'comunicaciones_values':comunicaciones_values
    }
    return render(request,"mistemplates/user-received-sent-messages.html", context)


@csrf_protect
@login_required
#@user_passes_test(communication_check)
def communication_table_review(request):
    user = request.user
    #user_area = Area.objects.get(users=user)
    user_areas = Area.objects.filter(users=user)

    all_communicationtable = CommunicationTable.objects.filter(area__in=user_areas).distinct()
    all_communicationtables = list(all_communicationtable)

    all_status = list(CommunicationTable.STATUS_CHOICES)

    context = {
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



def save_table_summarize_ia(request):

    if request.method == "POST":
        form_name = request.POST.get("form_name")

        if form_name == "save_table_summarize_form" :
            table_id = request.POST.get("table_id")
            new_summary = request.POST.get("summary")

            updated_table = CommunicationTable.objects.get(id=table_id)
            updated_table.summary=new_summary[:1000]
            updated_table.save() 


    return redirect('communications:communication_tables')

############# Views con IA
from ai_functions import implementation_functions as ai

def table_summarize_ia(request):
    assitant_answer = None
    max_tokens= 50

    all_communicationtables = CommunicationTable.objects.prefetch_related(
        'message__type',
        'message__receiver',
        'message__periodicity',
        )

    if request.method == "POST":
        table_id = request.POST.get("table_id")
        print("id tabla:", table_id)

        table = CommunicationTable.objects.filter(id=table_id)
        table_messages = CommunicationMessage.objects.filter(table__in=table).select_related("message")

        messages = [msg.message.name for msg in table_messages]

        data_input = "Messages:\n" + "\n".join(messages)
    
        user_input = "Summarize using less than 1000 characters the following  internal communication messages from a manufacturing company. Identify the general context, group messages by recurring topics if possible, and highlight the most relevant operational or quality-related issues. Be concise, avoid repetition, and focus on actionable or high-impact information. If applicable, you may mention aspects that relate to ISO 9001 principles, but it's not required.Do not use Markdown formatting or symbols, just text string."

        assitant_answer= ai.ai_text_function(data_input,user_input,max_tokens)

        print(assitant_answer)

    context = {
            "table_summary": assitant_answer,
            'all_communicationtables': all_communicationtables,
            "table_id": table_id,
            "open_summary_modal": True,
        }

    return render(request, "mistemplates/communication-tables.html", context)



def table_flow_map_ia(request):
    ia_flow_data = None
    table_id = None

    all_communicationtables = CommunicationTable.objects.all()

    if request.method == "POST":
        table_id = request.POST.get("table_id")
        if table_id:
            print("Generando mapa para tabla ID:", table_id)
            try:
                ia_flow_data = generate_communication_flow_map(table_id)
                print("Resultado IA:", ia_flow_data)
            except Exception as e:
                print(f"Error al generar mapa IA: {e}")
                ia_flow_data = {
                    "ia_insights": {
                        "patterns": [],
                        "weaknesses": [],
                        "conflicts": [],
                        "recommendations": [f"Error interno: {str(e)}"]
                    }
                }
        else:
            print("No se recibió table_id válido en POST")

    flow_ia_sections = None
    if ia_flow_data and "ia_insights" in ia_flow_data:
        flow_ia_sections = {
            "Patrones detectados": ia_flow_data["ia_insights"].get("patterns", []),
            "Debilidades o barreras de comunicación": ia_flow_data["ia_insights"].get("weaknesses", []),
            "Conflictos identificados": ia_flow_data["ia_insights"].get("conflicts", []),
            "Recomendaciones": ia_flow_data["ia_insights"].get("recommendations", []),
        }

    context = {
        "flow_ia_insights": ia_flow_data["ia_insights"] if ia_flow_data else None,
        "flow_ia_sections": flow_ia_sections,
        'all_communicationtables': all_communicationtables,
        "table_id": table_id,
        "open_flow_modal": True,
    }

    return render(request, "mistemplates/communication-tables.html", context)
