from django.db import models
from django import forms
from django.core.validators import RegexValidator

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
'''
######################## MATRIZ DE RIESGOS ########################
# Tabla de roles
class Role(models.Model):
    name = models.CharField(max_length=100, unique=True)  # Nombre del rol

    class Meta:
        db_table = 'tb_role'

    def __str__(self):
        return self.name  # Mostrar el nombre en texto
    
    def as_dict(self):
        return {
            "name": self.name
        }  
    

# Tabla de acciones de contención
class ContingencyAction(models.Model):
    name = models.CharField(max_length=255, unique=True)  # Nombre de la acción

    class Meta:
        db_table = 'tb_contingency_action'

    def __str__(self):
        return self.name  # Mostrar el nombre en texto
    
    def as_dict(self):
        return {
            "name": self.name
        }  


# Tabla de niveles de riesgo
class RiskLevel(models.Model):
    level = models.CharField(max_length=50, unique=True)  # Nivel de riesgo
    color = models.CharField(max_length=50)  # Color asociado al nivel

    class Meta:
        db_table = 'tb_risk_level'

    def __str__(self):
        return self.level  
    
    def as_dict(self):
        return {
            "level": self.level,
            "color": self.color
        }  


# Tabla de identificacion de riesgo
class RiskIdentification(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="risks")  # Relación con el departamento
    activity_name = models.CharField(max_length=255)  # Nombre de la actividad
    identified_risk = models.CharField(max_length=255, unique=True)  # Riesgo identificado
    consequences = models.TextField()  # Consecuencias del riesgo

    class Meta:
        db_table = 'tb_risk_identification'

    def __str__(self):
        return f"{self.identified_risk} ({self.department.name})"  # Mostrar riesgo y departamento
    
    def as_dict(self):
        return {
            "department": self.department,
            "activity_name": self.activity_name,
            "identified_risk": self.identified_risk,
            "consequences": self.consequences,
        }  


# Tabla de evaluación de riesgo
class RiskEvaluation(models.Model):
    SEVERITY_CHOICES = [(i, str(i)) for i in range(11)]  # Opciones para Severidad del 0 al 10
    OCCURRENCE_CHOICES = [(i, str(i)) for i in range(11)]  # Opciones para Ocurrencia del 0 al 10
    DETECTION_CHOICES = [(i, str(i)) for i in range(11)]  # Opciones para Detección del 0 al 10

    severity = models.IntegerField(choices=SEVERITY_CHOICES, verbose_name="Severity")  # Severidad (0-10)
    current_preventive_controls = models.TextField(blank=True, null=True, verbose_name="Current Preventive Controls")  # Controles actuales de prevención (opcional)
    occurrence = models.IntegerField(choices=OCCURRENCE_CHOICES, verbose_name="Occurrence")  # Ocurrencia (0-10)
    current_detection_controls = models.TextField(blank=True, null=True, verbose_name="Current Detection Controls")  # Controles actuales de detección (opcional)
    detection = models.IntegerField(choices=DETECTION_CHOICES, verbose_name="Detection")  # Detección (0-10)
    risk_level = models.ForeignKey(RiskLevel, on_delete=models.CASCADE, verbose_name="Risk Level")  # Nivel de Riesgo (relación con tabla RiskLevel)

    class Meta:
        db_table = 'tb_risk_evaluation'
    
    def __str__(self):
        return (
            f"Risk Evaluation: Severity {self.severity}, "
            f"Occurrence {self.occurrence}, Detection {self.detection}"
        )
    
    def as_dict(self):
        return {
            "severity": self.severity,
            "current_preventive_controls": self.current_preventive_controls,
            "occurrence": self.occurrence,
            "current_detection_controls": self.current_detection_controls,
            "detection": self.detection,
            "risk_level": self.risk_level,
        }  
    

# Tabla de tratamiento de riesgo
class RiskTreatment(models.Model):
    treatment_action = models.TextField(verbose_name="Treatment Action")  # Tratamiento a realizar
    responsible = models.ManyToManyField(Role, verbose_name="Responsible")  # Relación muchos a muchos con Role
    target_date = models.DateField(verbose_name="Target Date")  # Fecha objetivo
    actual_date = models.DateField(verbose_name="Actual Date")  # Fecha real (opcional)

    class Meta:
        db_table = 'tb_risk_treatment'

    def __str__(self):
        return f"Risk Treatment: {self.treatment_action[:100]}"  # Mostrar los primeros 100 caracteres del tratamiento
    
    def as_dict(self):
        return {
            "treatment_action": self.treatment_action,
            "responsible": [responsible.as_dict() for responsible in self.responsible.all()],
            "target_date": self.target_date,
            "actual_date": self.actual_date,
        } 
    

# Tabla de planes de contingencia
class ContingencyPlan(models.Model):
    contingency_actions = models.ManyToManyField(ContingencyAction, verbose_name="Contingency Actions")  # Relación muchos a muchos con ContingencyAction
    responsible = models.ManyToManyField(Role, related_name="responsible_for_contingency",verbose_name="Responsible")  # Relación muchos a muchos con Role (responsables)
    communicate_to = models.ManyToManyField(Role, related_name="communicate_to_contingency",verbose_name="Communicate To")  # Relación muchos a muchos con Role (comunicar a)

    class Meta:
        db_table = 'tb_contingency_plan'

    def __str__(self):
        actions = ", ".join([action.name for action in self.contingency_actions.all()[:3]])  # Mostrar hasta 3 acciones
        return f"Contingency Plan: {actions}"
    
    def as_dict(self):
        return {
            "contingency_actions": [contingency_action.as_dict() for contingency_action in self.contingency_actions.all()],
            "responsible": [responsible.as_dict() for responsible in self.responsible.all()],
            "communicate_to": [communicate.as_dict() for communicate in self.communicate_to.all()],
        } 
    

# Tabla de reevaluacion
class Reevaluation(models.Model):
    severity = models.PositiveIntegerField(choices=[(i, i) for i in range(11)], default=0)  # Severidad de 0 a 10
    occurrence = models.PositiveIntegerField(choices=[(i, i) for i in range(11)], default=0)  # Ocurrencia de 0 a 10
    detection = models.PositiveIntegerField(choices=[(i, i) for i in range(11)], default=0)  # Detección de 0 a 10
    risk_level = models.ForeignKey(RiskLevel, on_delete=models.CASCADE, related_name='reevaluations')  # Relación con RiskLevel (solo level)

    class Meta:
        db_table = 'tb_reevaluation'

    def __str__(self):
        return f"Reevaluation of risk level {self.risk_level.level} - Severity: {self.severity}, Occurrence: {self.occurrence}, Detection: {self.detection}"
    
    def as_dict(self):
        return {
            "severity": self.severity,
            "occurrence": self.occurrence,
            "detection": self.detection,
            "risk_level": self.risk_level
        } 
    

# Tabla de ejecución
class Execution(models.Model):
    created_by = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='executed_by')  # Elaboró (Creado por)
    reviewed_by = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='reviewed_by')  # Revisó (Revisado por)
    approved_by = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='approved_by')  # Aprobó (Aprobado por)

    class Meta:
        db_table = 'tb_execution'

    def __str__(self):
        return f"Execution: Created by {self.created_by.name}, Reviewed by {self.reviewed_by.name}, Approved by {self.approved_by.name}"
    
    def as_dict(self):
        return {
            "created_by": self.created_by,
            "reviewed_by": self.reviewed_by,
            "approved_by": self.approved_by
        } 
    

# Tabla de revision
class Revision(models.Model):
    code_validator = RegexValidator(
        regex=r'^[A-Za-z]{3}-[A-Za-z]{3}-\d{2}$',  # Formato: 3 letras - 3 letras - 2 números
        message='El código debe tener el formato: LLL-LLL-CC',
    )

    code = models.CharField(max_length=10, validators=[code_validator], unique=True, blank=True, null=True) #blank permite valores vacios en formulario,null en la base de datos
    review_number = models.IntegerField(choices=[(i, str(i)) for i in range(1, 11)], blank=True, null=True)
    review_date = models.DateField(blank=True, null=True)
    update_date = models.DateField(blank=True, null=True)

    class Meta:
        db_table = 'tb_revision'

    def __str__(self):
        return f"Revision {self.code} - {self.revision}"
    
    def as_dict(self):
        return {
            "code": self.code,
            "review_number": self.review_number,
            "review_date": self.review_date,
            "review_number": self.review_number,
            "update_date": self.update_date
        } '
        ''
'''