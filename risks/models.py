from django.db import models
from django.contrib.auth.models import User
from company.models import Area  
from django.core.validators import RegexValidator

# Tabla de roles
class Role(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = 'tb_risks_role'

    def __str__(self):
        return self.name
    
    def as_dict(self):
        return {
            "name": self.name
        }  

# Tabla de acciones de contención
class ContingencyAction(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        db_table = 'tb_risks_contingency_action'

    def __str__(self):
        return self.name
    
    def as_dict(self):
        return {
            "name": self.name
        }  

# Tabla de niveles de riesgo
class RiskLevel(models.Model):
    level = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=50)

    class Meta:
        db_table = 'tb_risks_level'

    def __str__(self):
        return self.level  
    
    def as_dict(self):
        return {
            "level": self.level,
            "color": self.color
        }  

# Tabla de identificación de riesgo
class RiskIdentification(models.Model):
    area = models.ForeignKey(Area, on_delete=models.CASCADE, related_name="risks")  
    activity_name = models.CharField(max_length=255)
    identified_risk = models.CharField(max_length=255, unique=True)
    consequences = models.TextField()

    class Meta:
        db_table = 'tb_risks_identification'

    def __str__(self):
        return f"{self.identified_risk} ({self.area.name})"
    
    def as_dict(self):
        return {
            "area": self.area.as_dict(),
            "activity_name": self.activity_name,
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
    responsible = models.ManyToManyField(User)
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
                "id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email
            } for user in self.responsible.all()],
            "target_date": self.target_date,
            "actual_date": self.actual_date,
        }


# Tabla de planes de contingencia
class ContingencyPlan(models.Model):
    risk = models.ForeignKey('RiskIdentification', on_delete=models.CASCADE, related_name='actions')
    contingency_actions = models.ManyToManyField('ContingencyAction')
    responsible = models.ManyToManyField(User, related_name="responsible_for_contingency")
    communicate_to = models.ManyToManyField(User, related_name="communicate_to_contingency")

    class Meta:
        db_table = 'tb_risks_contingency_plan'

    def __str__(self):
        actions = ", ".join([action.name for action in self.contingency_actions.all()[:3]])
        return f"Contingency Plan: {actions}"

    def as_dict(self):
        return {
            "contingency_actions": [action.as_dict() for action in self.contingency_actions.all()],
            "responsible": [{
                "id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email
            } for user in self.responsible.all()],
            "communicate_to": [{
                "id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email
            } for user in self.communicate_to.all()],
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


