from django.db import models
from django import forms
from django.core.validators import RegexValidator

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
    risk = models.ForeignKey(RiskIdentification, on_delete=models.CASCADE, related_name='evaluations')  # Añadir relación
    SEVERITY_CHOICES = [(i, str(i)) for i in range(11)]
    OCCURRENCE_CHOICES = [(i, str(i)) for i in range(11)]
    DETECTION_CHOICES = [(i, str(i)) for i in range(11)]

    severity = models.IntegerField(choices=SEVERITY_CHOICES, verbose_name="Severity")
    current_preventive_controls = models.TextField(blank=True, null=True, verbose_name="Current Preventive Controls")
    occurrence = models.IntegerField(choices=OCCURRENCE_CHOICES, verbose_name="Occurrence")
    current_detection_controls = models.TextField(blank=True, null=True, verbose_name="Current Detection Controls")
    detection = models.IntegerField(choices=DETECTION_CHOICES, verbose_name="Detection")
    risk_level = models.ForeignKey(RiskLevel, on_delete=models.CASCADE, verbose_name="Risk Level")

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
    risk = models.ForeignKey(RiskIdentification, on_delete=models.CASCADE, related_name='treatments')  # Añadir relación
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
    risk = models.ForeignKey(RiskIdentification, on_delete=models.CASCADE, related_name='actions')  # Añadir relación
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
    risk = models.ForeignKey(RiskIdentification, on_delete=models.CASCADE, related_name='reevaluations')  # Añadir relación
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
    
