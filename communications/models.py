from django.db import models
from django import forms
from django.core.validators import RegexValidator
from audits.models import Area
from company.models import Position
from django.contrib.auth.models import Group, User
# Create your models here.

######################## TABLAS DE COMUNICACIONES ########################

# Tabla de tipos de comunicacion
class CommunicationType(models.Model): 
    scope = models.CharField(max_length=50) 
    direction = models.CharField(max_length=50) 
    
    class Meta:
        db_table = 'tb_communication_type'

    def __str__(self):
        return f"{self.scope} {self.direction}"

    def as_dict(self):
        return {
            "scope":self.scope,
            "direction":self.direction,
        }


# Tabla de canales de comunicacion
class Channel(models.Model):
    name = models.CharField(max_length=50, unique=True)
       
    class Meta:
        db_table = 'tb_communication_channel'

    def __str__(self):
        return f"{self.name}"

    def as_dict(self):
        return {
            "name":self.name,
        }


# Tabla de periodicidades
class Periodicity(models.Model):
    name = models.CharField(max_length=50, unique=True)
       
    class Meta:
        db_table = 'tb_communication_periodicity'

    def __str__(self):
        return f"{self.name}"   

    def as_dict(self):
        return {
            "name":self.name,
        } 

class Message(models.Model):
    name = models.CharField(max_length=240, verbose_name="Asunto del Mensaje", blank=False, null=False)

    class Meta:
        db_table = 'tb_communication_message'  # Nombre de la tabla
        

    def as_dict(self):
        return {
            "id": self.id,
            "name": self.name,
        }
 


# Tabla de tablas de comunicacion
class CommunicationTable(models.Model):
    code_validator = RegexValidator(
        regex=r'^[A-Za-z]{3}-[A-Za-z]{3}-\d{2}$',  # Formato: 3 letras - 3 letras - 2 números
        message='El código debe tener el formato: LLL-LLL-CC',
    )

    STATUS_CHOICES = [
        ('pending_revision', 'Pendiente de Revisión'),
        ('pending_approve', 'Pendiente de Aprobación'),
        ('reviewed', 'Revisada'),
        ('approved', 'Aprobada'),
        ('open', 'Abierta (Aceptando Mensajes)'),
    ]

    code = models.CharField(max_length=50, validators=[code_validator], blank=False, unique=False) # Codigo de la tabla
    review_number = models.SmallIntegerField() # Revision
    review_date = models.DateField() # Fecha, formato estandar de Django y/m/d, esto se puede cambiar en html o formularios, pero no en modelo
    created_by = models.ForeignKey(Position, on_delete=models.PROTECT, related_name="created_by", blank=False) # Elaborado por
    reviewed_by = models.ForeignKey(Position, on_delete=models.PROTECT, related_name="reviewed_by", blank=True, null=True) # Revisado por
    approved_by = models.ForeignKey(Position, on_delete=models.PROTECT, related_name="approved_by", blank=True, null=True) # Aprobado por
    emiter = models.ForeignKey(Position, on_delete=models.PROTECT, related_name="emiter", blank=True, null=True)
    #area = models.ForeignKey(Area, on_delete=models.PROTECT, related_name="area", blank=True, null=True) 
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open', null=True)   
    summary = models.CharField(max_length=1000, verbose_name="Resumen", blank=True, null=True)

    class Meta:
        db_table = 'tb_communication_table'  # Nombre de la tabla
        ordering = ['id']  # Orden por ID

    def __str__(self):
        return(
            f"Tabla de comunicación: "
            f"Code: {self.code}, "
            f"Review Number: {self.review_number}, "
            f"Review Date: {self.review_date}, "
            f"Created by: {self.created_by}, "
            f"Reviewed by: {self.reviewed_by}, "
            f"Approved by: {self.approved_by}"
            f"Estado: {self.status}")

    def as_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "review_number": self.review_number,
            "review_date": self.review_date,
            "created_by": self.created_by,
            "reviewed_by": self.reviewed_by,
            "approved_by": self.approved_by,
        }   


class MessageChanel(models.Model):
    message = models.ForeignKey(Message, on_delete=models.PROTECT, related_name="message_channels", verbose_name="Message", null=False)
    channel = models.ForeignKey(Channel, on_delete=models.PROTECT, related_name="message_channels", verbose_name="Channel", null=False)

    class Meta:
        db_table = 'tb_communication_channels'  # Nombre de la tabla


# Tabla de mensajes
class CommunicationMessage(models.Model):
    type = models.ForeignKey(CommunicationType, on_delete=models.PROTECT, related_name="communication_type", verbose_name="Communication Type", null=False)
    message = models.ForeignKey(Message, on_delete=models.PROTECT, related_name="communication_message", verbose_name="Message", null=False)
    table = models.ForeignKey(CommunicationTable, on_delete=models.PROTECT, related_name="message", verbose_name="Table", null=False)
    receiver = models.ForeignKey(Position, on_delete=models.PROTECT, related_name="communication_receivers", verbose_name="Receptor")
    periodicity = models.ForeignKey(Periodicity, on_delete=models.PROTECT, related_name="communication_periodicity", verbose_name="Periodicity of Communication", null=False)
    
    
    class Meta:
        db_table = 'tb_communication_messages'  # Nombre de la tabla
        

    def as_dict(self):
        return {
            "id": self.id,
            "type": self.type.as_dict(),
            "table":self.table,
            "message": self.message,
            "periodicity": self.periodicity.as_dict(),
        }


#Formularios
'''
class MessageForm(forms.ModelForm): #Crea un formulario a partir del modelo ya creado
    class Meta:
       model = Message
       fields = [
           "communication_type", 
           "subject", 
           "channels", 
           "transmitter",
           "receivers",
           "periodicity"
        ]
'''