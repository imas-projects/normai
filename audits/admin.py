from django.contrib import admin
from . import models

# Registrar los modelos del sistema de auditoría
admin.site.register(models.AuditProgramHeader)
admin.site.register(models.Process)
admin.site.register(models.ProcessRequirement)
admin.site.register(models.AnnualProgram)
admin.site.register(models.AnnualProgramUser)
admin.site.register(models.AnnualPlan)
admin.site.register(models.AnnualPlanAuditor)
admin.site.register(models.Findings)
admin.site.register(models.AuditReport)
