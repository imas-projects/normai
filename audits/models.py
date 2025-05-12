from django.db import models
from django.contrib.auth.models import User
from company.models import Area, Requirement  
from processes.models import Process


class AuditProgramHeader(models.Model):
    year = models.IntegerField(verbose_name="Year")
    objective = models.TextField(verbose_name="Objective")
    scope = models.TextField(verbose_name="Scope")
    audit_criteria = models.TextField(verbose_name="Audit Criteria")
    security_standards = models.TextField(verbose_name="Security Standards")

    def __str__(self):
        return f"{self.year} - {self.objective[:50]}"

    class Meta:
        db_table = 'tb_audit_annual_program_headers'

    def as_dict(self):
        return {
            "id": self.id,
            "year": self.year,
            "objective": self.objective,
            "scope": self.scope,
            "audit_criteria": self.audit_criteria,
            "security_standards": self.security_standards,
        }

class ProcessRequirement(models.Model):
    process = models.ForeignKey(
        Process,
        on_delete=models.CASCADE
    )
    requirement = models.ForeignKey(
        'company.Requirement',  
        on_delete=models.CASCADE
    )

    class Meta:
        db_table = 'tb_audit_process_requirements'
        unique_together = ('process', 'requirement')

    def __str__(self):
        return f"{self.process.name} -> {self.requirement.name}"

class AnnualProgram(models.Model):
    program_header = models.ForeignKey(
        AuditProgramHeader,
        on_delete=models.PROTECT,
        related_name="annual_programs",
        verbose_name="Program Header"
    )
    process = models.ForeignKey(
        Process,
        on_delete=models.PROTECT,
        related_name="audit_annual_programs",
        verbose_name="Process"
    )
    month = models.PositiveSmallIntegerField(verbose_name="Month")

    def __str__(self):
        return f"{self.process.name} - {self.month}/{self.program_header.year}"

    class Meta:
        db_table = 'tb_audit_annual_program'

    def as_dict(self):
        return {
            "id": self.id,
            "program_header": self.program_header.as_dict(),
            "process": {
                "id": self.process.id,
                "name": self.process.name,
                "code": self.process.process_code
            },
            "month": self.month,
        }

class AnnualProgramUser(models.Model):
    annual_program = models.ForeignKey(
        AnnualProgram,
        on_delete=models.PROTECT,
        related_name="users",
        verbose_name="Annual Program"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="annual_programs",
        verbose_name="User"
    )

    class Meta:
        db_table = 'tb_audit_annual_program_users'
        unique_together = ('annual_program', 'user')

    def __str__(self):
        return f"{self.user.username} - {self.annual_program}"

    def as_dict(self):
        return {
            "id": self.id,
            "annual_program": self.annual_program.as_dict(),
            "user": {
                "id": self.user.id,
                "username": self.user.username,
                "first_name": self.user.first_name,
                "last_name": self.user.last_name,
                "email": self.user.email
            }
        }

class AnnualPlan(models.Model):
    annual_program = models.ForeignKey(
        AnnualProgram,
        on_delete=models.PROTECT,
        related_name="annual_plans",
        verbose_name="Annual Program"
    )
    lider = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="annual_plans",
        verbose_name="Audit Leader"
    )
    audit_opening_date = models.DateField(verbose_name="Audit Opening Date")
    audit_opening_time = models.TimeField(verbose_name="Audit Opening Time")
    audit_opening_location = models.TextField(verbose_name="Audit Opening Location")
    audit_closing_date = models.DateField(verbose_name="Audit Closing Date")
    audit_closing_time = models.TimeField(verbose_name="Audit Closing Time")
    audit_closing_location = models.TextField(verbose_name="Audit Closing Location")

    def __str__(self):
        return f"Audit Plan for {self.annual_program} ({self.audit_opening_date} to {self.audit_closing_date})"

    class Meta:
        db_table = 'tb_audit_annual_plan'

    def as_dict(self):
        return {
            "id": self.id,
            "annual_program": self.annual_program.as_dict(),
            "lider": {
                "id": self.lider.id,
                "username": self.lider.username,
                "first_name": self.lider.first_name,
                "last_name": self.lider.last_name,
                "email": self.lider.email
            },
            "audit_opening_date": self.audit_opening_date,
            "audit_opening_time": self.audit_opening_time,
            "audit_opening_location": self.audit_opening_location,
            "audit_closing_date": self.audit_closing_date,
            "audit_closing_time": self.audit_closing_time,
            "audit_closing_location": self.audit_closing_location,
        }

class AnnualPlanAuditor(models.Model):
    annual_plan = models.ForeignKey(
        AnnualPlan,
        on_delete=models.PROTECT,
        related_name="auditors",
        verbose_name="Audit Plan"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="auditors",
        verbose_name="Auditor"
    )

    class Meta:
        db_table = 'tb_audit_annual_plan_auditors'
        unique_together = ('annual_plan', 'user')

    def __str__(self):
        return f"{self.user.username} is an auditor for {self.annual_plan}"

    def as_dict(self):
        return {
            "audit_id": self.annual_plan.id,
            "user_id": self.user.id,
            "username": self.user.username,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
            "email": self.user.email,
        }
class AnnualPlanAudited(models.Model):
    annual_plan = models.ForeignKey(
        AnnualPlan,
        on_delete=models.PROTECT,
        related_name="audited_users",
        verbose_name="Audit Plan"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="audited_users",
        verbose_name="Audited User"
    )

    class Meta:
        db_table = 'tb_audit_annual_plan_audited'
        unique_together = ('annual_plan', 'user')

    def __str__(self):
        return f"{self.user.username} is audited for {self.annual_plan}"

    def as_dict(self):
        return {
            "audit_id": self.annual_plan.id,
            "user_id": self.user.id,
            "username": self.user.username,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
            "email": self.user.email,
        }

class Checklist(models.Model):
    audit_plan = models.ForeignKey(
        AnnualPlan,  
        on_delete=models.PROTECT,
        related_name="checklists",
        verbose_name="Audit Plan"
    )
    question = models.ForeignKey(
        'AuditedEvaluationQuestion',  
        on_delete=models.PROTECT,
        related_name="checklists",
        verbose_name="Question"
    )
    orden = models.PositiveSmallIntegerField(verbose_name="Order")
    compliance = models.BooleanField(verbose_name="Compliance")
    evidence = models.TextField(verbose_name="Objective Evidence", null=True, blank=True)

    def __str__(self):
        return f"Checklist for {self.question.question_text}"

    class Meta:
        db_table = 'tb_audit_checklist'
        ordering = ['orden']

    def as_dict(self):
        return {
            "id": self.id,
            "audit_id": self.audit_plan.id,
            "question_id": self.question.id,
            "question_text": self.question.question_text,
            "orden": self.orden,
            "compliance": self.compliance,
            "evidence": self.evidence,
        }

class AuditedEvaluationQuestion(models.Model):
    requirement = models.ForeignKey(
        Requirement,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Requirement"
    )
    question_text = models.TextField(verbose_name="Question Text")

    def __str__(self):
        return self.question_text

    class Meta:
        db_table = 'tb_audit_checklist_questions'

    def as_dict(self):
        return {
            "id": self.id,
            "requirement": self.requirement.as_dict() if self.requirement else None,
            "question_text": self.question_text,
        }
class AuditorEvaluation(models.Model):
    audit = models.ForeignKey(
        'AnnualPlan',  
        on_delete=models.PROTECT,
        related_name="auditor_evaluations",
        verbose_name="Audit"
    )
    question = models.ForeignKey(
        'AuditedEvaluationQuestion',  
        on_delete=models.PROTECT,
        related_name="auditor_evaluations",
        verbose_name="Question"
    )
    orden = models.SmallIntegerField(verbose_name="Order in Checklist")
    rate = models.IntegerField(verbose_name="Assigned Rating")

    def __str__(self):
        return f"Evaluation for {self.question.question_text} on {self.audit}"

    class Meta:
        db_table = 'tb_audit_auditor_evaluation'

    def as_dict(self):
        return {
            "id": self.id,
            "audit": self.audit.as_dict(),
            "question": self.question.as_dict(),
            "orden": self.orden,
            "rate": self.rate,
        }

class LeadAuditorEvaluationQuestion(models.Model):
    question_text = models.TextField(verbose_name="Question Text")
    type = models.TextField(choices=[('AUDITADO', 'AUDITADO'), ('AUDITOR_LIDER', 'AUDITOR_LIDER')], verbose_name="Type")

    def __str__(self):
        return self.question_text

    class Meta:
        db_table = 'tb_audit_auditor_questions'

    def as_dict(self):
        return {
            "id": self.id,
            "question_text": self.question_text,
            "type": self.type,
        }


class Findings(models.Model):
    report = models.ForeignKey(
        'AuditReport',  
        on_delete=models.PROTECT,
        verbose_name="Audit Report"
    )
    requirement = models.ForeignKey(
        'company.Requirement', 
        on_delete=models.PROTECT,
        null=True, 
        blank=True,
        verbose_name="Requirement"
    )
    finding_text = models.TextField(verbose_name="Finding")
    classification = models.CharField(
        max_length=20,
        verbose_name="Finding Classification",
        choices=[
            ('NC_MAYOR', 'NC_MAYOR'),
            ('NC_MENOR', 'NC_MENOR'),
            ('OPORTUNIDAD_MEJORA', 'OPORTUNIDAD_MEJORA'),
        ]
    )

    def __str__(self):
        return self.finding_text[:50]

    class Meta:
        db_table = 'tb_audit_findings'

    def clean(self):
        if self.classification not in ['NC_MAYOR', 'NC_MENOR', 'OPORTUNIDAD_MEJORA']:
            raise ValidationError('Invalid classification value.')

    def as_dict(self):
        return {
            "id": self.id,
            "report_id": self.report.id,  
            "requirement_id": self.requirement.id if self.requirement else None,
            "finding_text": self.finding_text,
            "classification": self.classification,
        }

class AuditReport(models.Model):
    audit = models.ForeignKey(
        'AnnualProgram', 
        on_delete=models.PROTECT,
        verbose_name="Audit Plan"
    )
    summary = models.TextField(verbose_name="Summary of Audit Development")
    strengths = models.TextField(verbose_name="Strengths")

    def __str__(self):
        return self.summary[:50]

    class Meta:
        db_table = 'tb_audit_report'

    def as_dict(self):
        return {
            "id": self.id,
            "audit_id": self.audit.id,  
            "summary": self.summary,
            "strengths": self.strengths,
        }

