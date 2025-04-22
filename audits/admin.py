from django.contrib import admin
from .models import (
    AuditRole, AuditTeam,
    Requirement, Checklist, Audited, AuditedEvaluationQuestion,
    LeadAuditorEvaluationQuestion, AuditProgramHeader, AnnualProgram,
    AuditPlanHeader, AssociatedElements, AuditorEvaluation,
    Findings, AuditReport
)

admin.site.register(Position)
admin.site.register(AuditRole)
admin.site.register(AuditTeam)
admin.site.register(Checklist)
admin.site.register(Audited)
admin.site.register(AuditedEvaluationQuestion)
admin.site.register(LeadAuditorEvaluationQuestion)
admin.site.register(AuditProgramHeader)
admin.site.register(AnnualProgram)
admin.site.register(AuditPlanHeader)
admin.site.register(AssociatedElements)
admin.site.register(AuditorEvaluation)
admin.site.register(Findings)
admin.site.register(AuditReport)
