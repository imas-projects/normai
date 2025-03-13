from django.db import models
from django import forms
from django.core.validators import RegexValidator
from risks.models import Department
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

'''
# Tabla de departamentos
class Department(models.Model):
    name = models.CharField(max_length=50, unique=True)
       
    class Meta:
        db_table = 'tb_department'

    def __str__(self):
        return f"{self.name}"

    def as_dict(self):
        return {
            "name":self.name,
        }
'''       

# Tabla de canales de comunicacion
class Channel(models.Model):
    name = models.CharField(max_length=50, unique=True)
       
    class Meta:
        db_table = 'tb_channel'

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
        db_table = 'tb_periodicity'

    def __str__(self):
        return f"{self.name}"   

    def as_dict(self):
        return {
            "name":self.name,
        } 


# Tabla de mensajes
class Message(models.Model):
    communication_type = models.ForeignKey(CommunicationType, on_delete=models.PROTECT, related_name="communication_type", verbose_name="Communication Type", null=False)
    subject = models.CharField(max_length=240, verbose_name="Asunto del Mensaje", blank=False, null=False)
    channels = models.ManyToManyField(Channel, related_name="channels", verbose_name="Communication Channel")
    transmitter = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="transmitter", verbose_name="Emisor", null=False)
    receivers = models.ManyToManyField(Department, related_name="message_receivers", verbose_name="Receptor")
    periodicity = models.ForeignKey(Periodicity, on_delete=models.PROTECT, related_name="message_periodicity", verbose_name="Periodicity of Communicaation", null=False)
    creation_date = models.DateTimeField(auto_now_add=True, null=False)
    update_date = models.DateTimeField(auto_now=True, null=False)
    
    def __str__(self):
        return f"Message -> Subject:{self.subject}"

    class Meta:
        db_table = 'tb_message'  # Nombre de la tabla
        

    def as_dict(self):
        return {
            "id": self.id,
            "communication_type": self.communication_type.as_dict(),
            "subject": self.subject,
            "channels": [channel.as_dict() for channel in self.channels.all()],
            "transmitter": self.transmitter.as_dict(),
            "receivers": [receiver.as_dict() for receiver in self.receivers.all()],
            "periodicity": self.periodicity.as_dict(),
        }


# Tabla de tablas de comunicacion
class CommunicationTable(models.Model):
    code_validator = RegexValidator(
        regex=r'^[A-Za-z]{3}-[A-Za-z]{3}-\d{2}$',  # Formato: 3 letras - 3 letras - 2 números
        message='El código debe tener el formato: LLL-LLL-CC',
    )

    code = models.CharField(max_length=50, validators=[code_validator], blank=False, unique=True) # Codigo de la tabla
    review_number = models.SmallIntegerField() # Revision
    review_date = models.DateField() # Fecha, formato estandar de Django y/m/d, esto se puede cambiar en html o formularios, pero no en modelo
    messages = models.ManyToManyField(Message, related_name="messages") # Message. Relacion many-to-many para poder almacenar todos los mensajes necesarios
    created_by = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="created_by", blank=False) # Elaborado por
    reviewed_by = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="reviewed_by", blank=True, default="Pending Review") # Revisado por
    approved_by = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="approved_by", blank=True, default="Pending Approval") # Aprobado por
   
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
            f"Approved by: {self.approved_by}") 

    def as_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "review_number": self.review_number,
            "review_date": self.review_date,
            "messages": [message.as_dict() for message in self.messages.all()],
            "created_by": self.created_by.as_dict(),
            "reviewed_by": self.reviewed_by.as_dict(),
            "approved_by": self.approved_by.as_dict(),
        }    

#Formularios
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