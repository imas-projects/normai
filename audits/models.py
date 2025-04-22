from django.db import models
from django.contrib.auth.models import User
from company.models import Area, Requirement  # Importación correcta del modelo Requirement

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

class Process(models.Model):
    name = models.CharField(max_length=200, verbose_name="Process Name")
    requirements = models.ManyToManyField(
        'company.Requirement',  # Referencia correcta a 'company.Requirement'
        through='ProcessRequirement',
        related_name="processes",
        verbose_name="Associated Requirements"
    )

    class Meta:
        db_table = 'tb_audit_process'

    def __str__(self):
        return self.name

    def as_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "requirements": [r.as_dict() for r in self.requirements.all()],
        }

class ProcessRequirement(models.Model):
    process = models.ForeignKey(
        Process,
        on_delete=models.CASCADE
    )
    requirement = models.ForeignKey(
        'company.Requirement',  # Correcto: Referencia a 'company.Requirement'
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
        related_name="annual_programs",
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
            "process": self.process.as_dict(),
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

class Findings(models.Model):
    report = models.ForeignKey(
        'AuditReport',  # Relacionado con el modelo AuditReport
        on_delete=models.PROTECT,
        verbose_name="Audit Report"
    )
    requirement = models.ForeignKey(
        'company.Requirement',  # Referencia correcta a 'company.Requirement'
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
            "report_id": self.report.id,  # Relacionado con el ID del reporte de auditoría
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
            "audit_id": self.audit.id,  # Relacionado con el ID del plan de auditoría
            "summary": self.summary,
            "strengths": self.strengths,
        }
