from django.contrib import admin
from . import models

# Registrar todos los modelos del sistema de auditoría
admin.site.register(models.AuditProgramHeader)
admin.site.register(models.ProcessRequirement)
admin.site.register(models.AnnualProgram)
admin.site.register(models.AnnualPlan)
admin.site.register(models.AnnualPlanAuditor)
admin.site.register(models.AnnualPlanAudited)
admin.site.register(models.Checklist)
admin.site.register(models.AuditedEvaluationQuestion)
admin.site.register(models.AuditorEvaluation)
admin.site.register(models.LeadAuditorEvaluationQuestion)
admin.site.register(models.Findings)
admin.site.register(models.AuditReport)
admin.site.register(models.ComplianceSnapshot)