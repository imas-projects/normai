from django.db import models
from django.contrib.auth.models import User
from company.models import Area, Position
from django.core.validators import RegexValidator
from multiselectfield import MultiSelectField
from processes.models import Process


# Tabla de identificación de riesgo
class RiskIdentification(models.Model):
    area = models.ForeignKey(Area, on_delete=models.CASCADE, related_name="risks")  
    process = models.ForeignKey(Process, on_delete=models.CASCADE, related_name="risks")
    identified_risk = models.CharField(max_length=255, unique=True)
    consequences = models.TextField()

    class Meta:
        db_table = 'tb_risks_identification'

    def __str__(self):
        return f"{self.identified_risk} ({self.process.name} - {self.area.name})"

    def as_dict(self):
        return {
            "area": self.area.as_dict(),
            "process": self.process.name,
            "identified_risk": self.identified_risk,
            "consequences": self.consequences,
        }

# Tabla de evaluación de riesgo
class RiskEvaluation(models.Model):
    SEVERITY_CHOICES = [(i, str(i)) for i in range(11)]
    OCCURRENCE_CHOICES = [(i, str(i)) for i in range(11)]
    DETECTION_CHOICES = [(i, str(i)) for i in range(11)]
    RISK_LEVEL_CHOICES = [
        ('High', 'High'),
        ('Moderate', 'Moderate'),
        ('Low', 'Low')
    ]

    severity = models.IntegerField(choices=SEVERITY_CHOICES)
    current_preventive_controls = models.TextField(blank=True, null=True)
    occurrence = models.IntegerField(choices=OCCURRENCE_CHOICES)
    current_detection_controls = models.TextField(blank=True, null=True)
    detection = models.IntegerField(choices=DETECTION_CHOICES)
    risk_level = models.CharField(max_length=10, choices=RISK_LEVEL_CHOICES)
    risk = models.ForeignKey('RiskIdentification', on_delete=models.CASCADE, related_name='evaluations', blank=True, null=True)

    class Meta:
        db_table = 'tb_risks_evaluation'

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
            "risk_level": self.risk_level
        }


# Tabla de tratamiento de riesgo
class RiskTreatment(models.Model):
    risk = models.ForeignKey('RiskIdentification', on_delete=models.CASCADE, related_name='treatments')
    treatment_action = models.TextField()
    responsible = models.ManyToManyField(Position)  # Cambio aquí
    target_date = models.DateField()
    actual_date = models.DateField()

    class Meta:
        db_table = 'tb_risks_treatment'

    def __str__(self):
        return f"Risk Treatment: {self.treatment_action[:100]}"

    def as_dict(self):
        return {
            "treatment_action": self.treatment_action,
            "responsible": [{
                "id": position.id,
                "name": position.name,
                "code": position.code,
                "area": {
                    "id": position.area.id,
                    "name": position.area.name
                }
            } for position in self.responsible.all()],
            "target_date": self.target_date,
            "actual_date": self.actual_date,
        }



# Tabla de planes de contingencia
class ContingencyPlan(models.Model):
    ACTION_CHOICES = [
        ("N/A", "N/A"),
        ("ALT_PROCEDURES", "Establecer procedimientos alternativos"),
        ("ALT_SUPPLIERS", "Identificar proveedores sustitutos"),
        ("BACKUP_STAFF", "Asignar personal de respaldo"),
        ("EMERGENCY_STOCK", "Mantener inventarios de emergencia"),
        ("TECH_REDUNDANCY", "Implementar redundancias tecnológicas"),
        ("CRISIS_COMM", "Establecer protocolos de comunicación de crisis"),
        ("DRILLS", "Realizar simulacros y pruebas periódicas"),
        ("INSURANCE", "Contratar seguros o coberturas específicas"),
        ("OUTSOURCE", "Externalizar temporalmente operaciones críticas"),
        ("MANUALS", "Crear manuales de operación ante fallos"),
    ]

    risk = models.ForeignKey('RiskIdentification', on_delete=models.CASCADE, related_name='actions')
    contingency_actions = MultiSelectField(choices=ACTION_CHOICES)
    responsible = models.ManyToManyField(Position, related_name="responsible_for_contingency") 
    communicate_to = models.ManyToManyField(Position, related_name="communicate_to_contingency") 

    class Meta:
        db_table = 'tb_risks_contingency_plan'

    def __str__(self):
        actions = ", ".join([dict(self.ACTION_CHOICES).get(code) for code in self.contingency_actions[:3]])
        return f"Contingency Plan: {actions}"

    def as_dict(self):
        return {
            "contingency_actions": [dict(self.ACTION_CHOICES).get(code) for code in self.contingency_actions],
            "responsible": [{
                "id": position.id,
                "name": position.name,
                "code": position.code,
                "area": {
                    "id": position.area.id,
                    "name": position.area.name
                }
            } for position in self.responsible.all()],
            "communicate_to": [{
                "id": position.id,
                "name": position.name,
                "code": position.code,
                "area": {
                    "id": position.area.id,
                    "name": position.area.name
                }
            } for position in self.communicate_to.all()],
        }


# Tabla de reevaluación
class Reevaluation(models.Model):
    RISK_LEVEL_CHOICES = [
        ('High', 'High'),
        ('Moderate', 'Moderate'),
        ('Low', 'Low')
    ]

    risk = models.ForeignKey('RiskIdentification', on_delete=models.CASCADE, related_name='reevaluations')
    severity = models.PositiveIntegerField(choices=[(i, i) for i in range(11)], default=0)
    occurrence = models.PositiveIntegerField(choices=[(i, i) for i in range(11)], default=0)
    detection = models.PositiveIntegerField(choices=[(i, i) for i in range(11)], default=0)
    risk_level = models.CharField(max_length=10, choices=RISK_LEVEL_CHOICES)

    class Meta:
        db_table = 'tb_risks_reevaluation'

    def __str__(self):
        return f"Reevaluation - Risk Level: {self.risk_level}, Severity: {self.severity}, Occurrence: {self.occurrence}, Detection: {self.detection}"

    def as_dict(self):
        return {
            "severity": self.severity,
            "occurrence": self.occurrence,
            "detection": self.detection,
            "risk_level": self.risk_level
        }


