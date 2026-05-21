from django.db import models
from django.contrib.auth.models import User
from company.models import Area, Requirement  
from processes.models import Process
from django.core.exceptions import ValidationError
from standards.models import Standard, StandardRequirement




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
        StandardRequirement,
        on_delete=models.PROTECT,
        verbose_name="Standard Requirement"
    )

    class Meta:
        db_table = 'tb_audit_process_requirements'
    

    def __str__(self):
        return f"{self.process.name} -> {self.requirement}"

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
    standard = models.ForeignKey(
        'standards.Standard',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="annual_programs",
        verbose_name="Norma",
        help_text="Norma que se auditará en este programa"
    )

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
            "standard": {
                "id": self.standard.id,
                "name": self.standard.name,
            } if self.standard else None,
        }


class AnnualPlan(models.Model):
    annual_program = models.ForeignKey(
        AnnualProgram,
        on_delete=models.PROTECT,
        related_name="annual_plans",
        verbose_name="Annual Program"
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
        ProcessRequirement,
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

    @property
    def standard_requirement(self):
        """
        Acceso directo al StandardRequirement vinculado,
        sin necesidad de recorrer la cadena completa.
        Devuelve None si no hay requirement asignado.
        """
        if self.requirement and self.requirement.requirement:
            return self.requirement.requirement
        return None

    @property
    def clause(self):
        """
        Acceso directo a la Clause del requisito vinculado.
        """
        std_req = self.standard_requirement
        return std_req.clause if std_req else None

    @property
    def standard(self):
        """
        Acceso directo al Standard del requisito vinculado.
        """
        clause = self.clause
        return clause.standard if clause else None

    def as_dict(self):
        std_req = self.standard_requirement
        clause = self.clause
        standard = self.standard
        return {
            "id": self.id,
            "question_text": self.question_text,
            "requirement": {
                "text": std_req.text if std_req else None,
                "mandatory": std_req.mandatory if std_req else None,
                "criticality_level": std_req.criticality_level if std_req else None,
            } if std_req else None,
            "clause": {
                "code": clause.code if clause else None,
                "title": clause.title if clause else None,
            } if clause else None,
            "standard": {
                "name": standard.name if standard else None,
            } if standard else None,
        }
    
class AuditorEvaluation(models.Model):
    audit_plan = models.ForeignKey(
        'AnnualPlan',
        on_delete=models.PROTECT,
        related_name="auditor_evaluations",
        verbose_name="Audit Plan"
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
        return f"Evaluation for {self.question} on {self.audit_plan}"

    class Meta:
        db_table = 'tb_audit_auditor_evaluation'

    def as_dict(self):
        return {
            "id": self.id,
            "audit_plan": self.audit_plan.as_dict(),
            "question": self.question.as_dict(),
            "orden": self.orden,
            "rate": self.rate,
        }


class LeadAuditorEvaluationQuestion(models.Model):
    question_text = models.TextField(verbose_name="Question Text")
    type = models.TextField(choices=[('AUDITADO', 'Auditado'), ('AUDITOR_LIDER', 'Auditor Lider')], verbose_name="Type")

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
    audit_plan = models.ForeignKey(
        'AnnualPlan',
        on_delete=models.PROTECT,
        related_name="findings",
        verbose_name="Audit Plan"
    )
    requirement = models.ForeignKey(
        ProcessRequirement,
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
            ('NC_MAYOR', 'No Conformidad Mayor'),
            ('NC_MENOR', 'No Conformidad Menor'),
            ('OPORTUNIDAD_MEJORA', 'Oportunidad de mejora'),
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
            "audit_plan_id": self.audit_plan.id,
            "requirement": self.requirement.requirement.text if self.requirement else None,
            "finding_text": self.finding_text,
            "classification": self.classification,
        }

class AuditReport(models.Model):
    audit_plan = models.ForeignKey(
        'AnnualPlan',
        db_column='audit_plan_id',
        on_delete=models.PROTECT,
        verbose_name="Audit Plan"
    )
    summary = models.TextField(verbose_name="Summary of Audit Development")
    recommendations = models.TextField(verbose_name="Recommendations")  
    conclusions = models.TextField(verbose_name="Conclusions") 

    def __str__(self):
        return self.summary[:50]

    class Meta:
        db_table = 'tb_audit_report'

    def as_dict(self):
        return {
            "id": self.id,
            "audit_plan_id": self.audit_plan.id, 
            "summary": self.summary,
            "recommendations": self.recommendations,
            "conclusions": self.conclusions,
        }


class CorrectiveAction(models.Model):
    corrective_action = models.TextField(verbose_name="Corrective Action")
    due_date = models.DateField(verbose_name="Due Date")
    responsible_user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        verbose_name="Responsible User"
    )
    audit_report = models.ForeignKey(
        'AuditReport',
        on_delete=models.PROTECT,
        related_name="corrective_actions",
        verbose_name="Audit Report"
    )

    def __str__(self):
        return f"{self.corrective_action[:50]} (Due: {self.due_date})"

    class Meta:
        db_table = 'tb_audit_corrective_actions'

    def as_dict(self):
        return {
            "id": self.id,
            "corrective_action": self.corrective_action,
            "due_date": self.due_date,
            "responsible_user": {
                "id": self.responsible_user.id,
                "username": self.responsible_user.username,
                "email": self.responsible_user.email,
            },
            "audit_report_id": self.audit_report.id,
        }


class CorrectiveActionFollowUp(models.Model):
    corrective_action = models.ForeignKey(
        CorrectiveAction,
        on_delete=models.CASCADE,
        related_name="followups",
        verbose_name="Corrective Action"
    )
    followup_date = models.DateField(verbose_name="Follow-up Date")
    status = models.CharField(
        max_length=50,
        verbose_name="Status",
        choices=[
            ('PENDING', 'Pending'),
            ('IN_PROGRESS', 'In Progress'),
            ('COMPLETED', 'Completed'),
        ]
    )
    comments = models.TextField(verbose_name="Comments", null=True, blank=True)

    def __str__(self):
        return f"Follow-up on {self.corrective_action.id} - {self.status}"

    class Meta:
        db_table = 'tb_audit_corrective_actions_followup'

    def as_dict(self):
        return {
            "id": self.id,
            "corrective_action_id": self.corrective_action.id,
            "followup_date": self.followup_date,
            "status": self.status,
            "comments": self.comments,
        }

class ComplianceSnapshot(models.Model):
    """
    Persiste el resultado del cálculo de cumplimiento para un AnnualPlan.
    Permite comparación temporal entre auditorías (F3-03).
    """
    CATEGORY_CHOICES = [
        ('EXCELLENT', 'Excelente (≥85%)'),
        ('GOOD', 'Bueno (70-84%)'),
        ('PARTIAL', 'Parcial (50-69%)'),
        ('LOW', 'Bajo (25-49%)'),
        ('CRITICAL', 'Crítico (<25%)'),
    ]

    annual_plan = models.ForeignKey(
        AnnualPlan,
        on_delete=models.CASCADE,
        related_name='compliance_snapshots',
        verbose_name='Plan de Auditoría',
    )
    process = models.ForeignKey(
        Process,
        on_delete=models.PROTECT,
        related_name='compliance_snapshots',
        verbose_name='Proceso',
    )
    standard = models.ForeignKey(
        'standards.Standard',
        on_delete=models.PROTECT,
        related_name='compliance_snapshots',
        verbose_name='Norma',
    )
    score = models.FloatField(
        verbose_name='Puntuación (0.0 - 1.0)',
        help_text='Valor numérico del cumplimiento entre 0 y 1'
    )
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        verbose_name='Categoría de Cumplimiento',
    )
    total_requirements = models.IntegerField(
        verbose_name='Total de Requisitos',
    )
    compliant_count = models.IntegerField(
        verbose_name='Requisitos Conformes',
    )
    non_compliant_count = models.IntegerField(
        verbose_name='Requisitos No Conformes',
    )
    insufficient_count = models.IntegerField(
        verbose_name='Requisitos con Evidencia Insuficiente',
    )
    not_evaluated_count = models.IntegerField(
        verbose_name='Requisitos No Evaluados',
    )
    calculated_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Cálculo',
    )
    detail = models.JSONField(
        verbose_name='Desglose por Requisito',
        help_text='JSON con el detalle del cálculo por cada ProcessRequirement',
        default=dict,
    )

    class Meta:
        db_table = 'tb_compliance_snapshots'
        verbose_name = 'Snapshot de Cumplimiento'
        verbose_name_plural = 'Snapshots de Cumplimiento'
        ordering = ['-calculated_at']

    def __str__(self):
        return (
            f"{self.process.name} | {self.standard.name} | "
            f"{self.category} ({self.score:.1%}) | {self.calculated_at.date()}"
        )

    def as_dict(self):
        return {
            'id': self.id,
            'annual_plan_id': self.annual_plan.id,
            'process': {
                'id': self.process.id,
                'name': self.process.name,
            },
            'standard': {
                'id': self.standard.id,
                'name': self.standard.name,
            },
            'score': round(self.score * 100, 1),
            'category': self.category,
            'total_requirements': self.total_requirements,
            'compliant_count': self.compliant_count,
            'non_compliant_count': self.non_compliant_count,
            'insufficient_count': self.insufficient_count,
            'not_evaluated_count': self.not_evaluated_count,
            'calculated_at': self.calculated_at.isoformat(),
            'detail': self.detail,
        }