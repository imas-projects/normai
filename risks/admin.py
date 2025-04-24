from django.contrib import admin
from . import models


admin.site.register(models.Role)
admin.site.register(models.ContingencyAction)
admin.site.register(models.RiskLevel)
admin.site.register(models.RiskIdentification)
admin.site.register(models.RiskEvaluation)
admin.site.register(models.RiskTreatment)
admin.site.register(models.ContingencyPlan)
admin.site.register(models.Reevaluation)
