from django.db import models
from django.contrib.auth.models import User, Group

class ParentArea(models.Model):
    name = models.CharField(max_length=100, verbose_name="Parent Area Name", unique=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'tb_parent_area'

    def as_dict(self):
        return {"id": self.id, "name": self.name}

class Area(models.Model):
    parent_area = models.ForeignKey(ParentArea, on_delete=models.PROTECT, related_name="areas", verbose_name="Parent Area")
    name = models.CharField(max_length=100, verbose_name="Area Name")
    groups = models.ManyToManyField(Group, related_name="areas")
    users = models.ManyToManyField(User, related_name="areas")  

    def __str__(self):
        return f"{self.name} ({self.parent_area.name})"

    class Meta:
        db_table = 'tb_area'

    def as_dict(self):
        return {
            "id": self.id,
            "parent_area": self.parent_area.as_dict(),
            "name": self.name,
            "groups": [{"id": g.id, "name": g.name} for g in self.groups.all()],
            "users": [{
                "id": u.id,
                "username": u.username,
                "first_name": u.first_name,
                "last_name": u.last_name,
                "email": u.email
            } for u in self.users.all()],
        }

class Position(models.Model):
    parent_area = models.ForeignKey(ParentArea, on_delete=models.PROTECT, related_name="positions", verbose_name="Parent Area")
    area = models.ForeignKey(Area, on_delete=models.PROTECT, related_name="positions", verbose_name="Area")
    title = models.CharField(max_length=100, verbose_name="Job Title")

    def __str__(self):
        return f"{self.title} ({self.area.name} - {self.parent_area.name})"

    class Meta:
        db_table = 'tb_position'

    def as_dict(self):
        return {"id": self.id, "parent_area": self.parent_area.as_dict(), "area": self.area.as_dict(), "title": self.title}

class AuditRole(models.Model):
    name = models.CharField(max_length=100, verbose_name="Audit Team Role", unique=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'tb_audit_role'

    def as_dict(self):
        return {"id": self.id, "name": self.name}

class AuditTeam(models.Model):
    person = models.ForeignKey(User, on_delete=models.PROTECT, related_name="audit_roles", verbose_name="User")
    role = models.ForeignKey(AuditRole, on_delete=models.PROTECT, related_name="audit_members", verbose_name="Role")

    def __str__(self):
        return f"{self.person.get_full_name()} - {self.role.name}"

    class Meta:
        db_table = 'tb_audit_team'

    def as_dict(self):
        return {
            "id": self.id,
            "person": {
                "id": self.person.id,
                "username": self.person.username,
                "first_name": self.person.first_name,
                "last_name": self.person.last_name,
                "email": self.person.email,
            },
            "role": self.role.as_dict()
        }

class Requirement(models.Model):
    name = models.CharField(max_length=200, verbose_name="Requirement Name")
    parent = models.ForeignKey(
        'self', 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True, 
        related_name="sub_requirements"
    )

    def __str__(self):
        return f"{self.name}" if not self.parent else f"{self.name} (under {self.parent.name})"

    class Meta:
        db_table = 'tb_requirement'

    def as_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "parent": self.parent.as_dict() if self.parent else None,
        }

class Audited(models.Model):
    requirement = models.ForeignKey(Requirement, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Requirement")
    audited_user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="audited", verbose_name="Audited User")

    def __str__(self):
        return f"{self.audited_user.get_full_name()}"

    class Meta:
        db_table = 'tb_audited'

    def as_dict(self):
        return {
            "id": self.id,
            "requirement": self.requirement.as_dict() if self.requirement else None,
            "audited_user": {
                "id": self.audited_user.id,
                "username": self.audited_user.username,
                "first_name": self.audited_user.first_name,
                "last_name": self.audited_user.last_name,
                "email": self.audited_user.email,
            }
        }
    
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    position = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True, blank=True)

class AuditedEvaluationQuestion(models.Model):
    requirement = models.ForeignKey(Requirement, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Requirement")
    question_text = models.CharField(max_length=500, verbose_name="Question Text")
    order = models.IntegerField(verbose_name="Order")
    rating = models.CharField(max_length=200, verbose_name="Rating", null=True, blank=True)  

    def __str__(self):
        return self.question_text

    class Meta:
        db_table = 'tb_audited_evaluation_question'

    def as_dict(self):
        return {
            "id": self.id,
            "requirement": self.requirement.as_dict() if self.requirement else None,
            "question_text": self.question_text,
            "order": self.order,
            "rating": self.rating,  
        }


class LeadAuditorEvaluationQuestion(models.Model):
    requirement = models.ForeignKey(Requirement, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Requirement")
    question_text = models.CharField(max_length=500, verbose_name="Question Text")
    order = models.IntegerField(verbose_name="Order")
    rating = models.CharField(max_length=200, verbose_name="Rating", null=True, blank=True) 

    def __str__(self):
        return self.question_text

    class Meta:
        db_table = 'tb_lead_auditor_evaluation_question'

    def as_dict(self):
        return {
            "id": self.id,
            "requirement": self.requirement.as_dict() if self.requirement else None,
            "question_text": self.question_text,
            "order": self.order,
            "rating": self.rating,  
        }


class AuditProgramHeader(models.Model):
    objective = models.TextField(verbose_name="Objective")
    scope = models.TextField(verbose_name="Scope")
    audit_criteria = models.TextField(verbose_name="Audit Criteria")
    security_standards = models.TextField(verbose_name="Security Standards")

    def __str__(self):
        return self.objective[:50]

    class Meta:
        db_table = 'tb_audit_program_header'

    def as_dict(self):
        return {
            "id": self.id,
            "objective": self.objective,
            "scope": self.scope,
            "audit_criteria": self.audit_criteria,
            "security_standards": self.security_standards,
        }

class AnnualProgram(models.Model):
    requirement = models.ForeignKey(Requirement, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Requirement")
    month = models.IntegerField(verbose_name="Month")
    year = models.IntegerField(verbose_name="Year")

    def __str__(self):
        return f"{self.requirement} - {self.month}/{self.year}" if self.requirement else f"Program for {self.month}/{self.year}"

    class Meta:
        db_table = 'tb_annual_program'

    def as_dict(self):
        return {
            "id": self.id,
            "requirement": self.requirement.as_dict() if self.requirement else None,
            "month": self.month,
            "year": self.year,
        }

class AuditPlanHeader(models.Model):
    opening_meeting_location = models.CharField(max_length=200, verbose_name="Opening Meeting Location")
    opening_meeting_date_time = models.DateTimeField(verbose_name="Opening Meeting Date and Time")
    closing_meeting_location = models.CharField(max_length=200, verbose_name="Closing Meeting Location")
    closing_meeting_date_time = models.DateTimeField(verbose_name="Closing Meeting Date and Time")

    def __str__(self):
        return self.opening_meeting_location

    class Meta:
        db_table = 'tb_audit_plan_header'

    def as_dict(self):
        return {
            "id": self.id,
            "opening_meeting_location": self.opening_meeting_location,
            "opening_meeting_date_time": self.opening_meeting_date_time,
            "closing_meeting_location": self.closing_meeting_location,
            "closing_meeting_date_time": self.closing_meeting_date_time,
        }

class AssociatedElements(models.Model):
    requirement = models.ForeignKey(Requirement, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Requirement")
    audit_date = models.DateField(verbose_name="Audit Date")
    audit_time = models.CharField(max_length=50, verbose_name="Audit Time")
    audit_team_member = models.ForeignKey(AuditTeam, on_delete=models.PROTECT, verbose_name="Audit Team Member")
    audit_location = models.CharField(max_length=200, verbose_name="Audit Location")

    def __str__(self):
        return f"{self.requirement} - {self.audit_date} at {self.audit_time}" if self.requirement else f"Audit on {self.audit_date}"

    class Meta:
        db_table = 'tb_associated_elements'

    def as_dict(self):
        return {
            "id": self.id,
            "requirement": self.requirement.as_dict() if self.requirement else None,
            "audit_date": self.audit_date,
            "audit_time": self.audit_time,
            "audit_team_member": self.audit_team_member.as_dict(),
            "audit_location": self.audit_location,
        }

class Checklist(models.Model):
    requirement = models.ForeignKey(Requirement, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Requirement")
    question_text = models.CharField(max_length=500, verbose_name="Question Text")
    order = models.IntegerField(verbose_name="Order")

    objective_evidence = models.TextField(verbose_name="Objective Evidence", null=True, blank=True)
    compliance = models.TextField(verbose_name="Compliance", null=True, blank=True)

    def __str__(self):
        return self.question_text

    class Meta:
        db_table = 'tb_checklist'
        ordering = ['order']

    def as_dict(self):
        return {
            "id": self.id,
            "requirement": self.requirement.as_dict() if self.requirement else None,
            "question_text": self.question_text,
            "order": self.order,
            "objective_evidence": self.objective_evidence,
            "compliance": self.compliance,
        }

class AuditorEvaluation(models.Model):
    requirement = models.ForeignKey(Requirement, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Requirement")
    evaluation_date = models.DateField(verbose_name="Evaluation Date")

    def __str__(self):
        return f"Evaluation on {self.evaluation_date}"

    class Meta:
        db_table = 'tb_auditor_evaluation'

    def as_dict(self):
        return {
            "id": self.id,
            "requirement": self.requirement.as_dict() if self.requirement else None,
            "evaluation_date": self.evaluation_date,
        }
    
class Findings(models.Model):
    requirement = models.ForeignKey(Requirement, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Requirement")
    finding_text = models.TextField(verbose_name="Finding")
    classification = models.IntegerField(verbose_name="Finding Classification", choices=[(i, str(i)) for i in range(6)])  

    def __str__(self):
        return self.finding_text[:50]

    class Meta:
        db_table = 'tb_findings'

    def clean(self):
        if self.classification < 0 or self.classification > 5:
            raise ValidationError('Classification must be between 0 and 5.')

    def as_dict(self):
        return {
            "id": self.id,
            "requirement": self.requirement.as_dict() if self.requirement else None,
            "finding_text": self.finding_text,
            "classification": self.classification,
        }


class AuditReport(models.Model):
    requirement = models.ForeignKey(Requirement, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Requirement")
    summary = models.TextField(verbose_name="Summary of Audit Development")
    strengths = models.TextField(verbose_name="Strengths")

    def __str__(self):
        return self.summary[:50]  

    class Meta:
        db_table = 'tb_audit_report'

    def as_dict(self):
        return {
            "id": self.id,
            "requirement": self.requirement.as_dict() if self.requirement else None,
            "summary": self.summary,
            "strengths": self.strengths,
        }
