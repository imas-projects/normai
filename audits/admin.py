from django.contrib import admin
from . import models

# Register your models here.
admin.site.register(models.ParentArea)
admin.site.register(models.Area)
admin.site.register(models.Position)
admin.site.register(models.AuditRole)
admin.site.register(models.AuditTeam)
admin.site.register(models.RequirementLevel1)
admin.site.register(models.RequirementLevel2)
admin.site.register(models.RequirementLevel3)
admin.site.register(models.ChecklistQuestion)
admin.site.register(models.Audited)
admin.site.register(models.AuditedEvaluationQuestion)
admin.site.register(models.LeadAuditorEvaluationQuestion)
admin.site.register(models.AuditProgramHeader)
admin.site.register(models.AnnualProgram)
admin.site.register(models.AuditPlanHeader)
admin.site.register(models.AssociatedElements)
admin.site.register(models.Checklist)
admin.site.register(models.AuditorEvaluation)
admin.site.register(models.FindingClassification)
admin.site.register(models.Findings)
admin.site.register(models.AuditReport)


