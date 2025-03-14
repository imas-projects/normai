from django.db import models

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
    
    def __str__(self):
        return f"{self.name} ({self.parent_area.name})"
    
    class Meta:
        db_table = 'tb_area'
    
    def as_dict(self):
        return {"id": self.id, "parent_area": self.parent_area.as_dict(), "name": self.name}

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

class Person(models.Model):
    first_name = models.CharField(max_length=100, verbose_name="First Name")
    last_name = models.CharField(max_length=100, verbose_name="Last Name")
    parent_area = models.ForeignKey(ParentArea, on_delete=models.PROTECT, related_name="people", verbose_name="Parent Area")
    area = models.ForeignKey(Area, on_delete=models.PROTECT, related_name="people", verbose_name="Area")
    position = models.ForeignKey(Position, on_delete=models.PROTECT, related_name="employees", verbose_name="Job Position")
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.position.title} ({self.area.name} - {self.parent_area.name})"
    
    class Meta:
        db_table = 'tb_person'
    
    def as_dict(self):
        return {"id": self.id, "first_name": self.first_name, "last_name": self.last_name, "parent_area": self.parent_area.as_dict(), "area": self.area.as_dict(), "position": self.position.as_dict()}

class AuditRole(models.Model):
    name = models.CharField(max_length=100, verbose_name="Audit Team Role", unique=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'tb_audit_role'
    
    def as_dict(self):
        return {"id": self.id, "name": self.name}

class AuditTeam(models.Model):
    person = models.ForeignKey(Person, on_delete=models.PROTECT, related_name="audit_roles", verbose_name="Person")
    role = models.ForeignKey(AuditRole, on_delete=models.PROTECT, related_name="audit_members", verbose_name="Role")
    
    def __str__(self):
        return f"{self.person.first_name} {self.person.last_name} - {self.role.name}"
    
    class Meta:
        db_table = 'tb_audit_team'
    
    def as_dict(self):
        return {"id": self.id, "person": self.person.as_dict(), "role": self.role.as_dict()}

class RequirementLevel1(models.Model):
    name = models.CharField(max_length=200, verbose_name="Requirement Level 1")
    
    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'tb_requirement_level1'
    
    def as_dict(self):
        return {"id": self.id, "name": self.name}

class RequirementLevel2(models.Model):
    level1 = models.ForeignKey(RequirementLevel1, on_delete=models.PROTECT, related_name="level2_requirements", verbose_name="Requirement Level 1")
    name = models.CharField(max_length=200, verbose_name="Requirement Level 2")
    
    def __str__(self):
        return f"{self.name} ({self.level1.name})"
    
    class Meta:
        db_table = 'tb_requirement_level2'
    
    def as_dict(self):
        return {"id": self.id, "level1": self.level1.as_dict(), "name": self.name}

class RequirementLevel3(models.Model):
    level1 = models.ForeignKey(RequirementLevel1, on_delete=models.PROTECT, related_name="level3_requirements", verbose_name="Requirement Level 1")
    level2 = models.ForeignKey(RequirementLevel2, on_delete=models.PROTECT, related_name="level3_requirements", verbose_name="Requirement Level 2")
    name = models.CharField(max_length=200, verbose_name="Requirement Level 3")
    
    def __str__(self):
        return f"{self.name} ({self.level2.name} - {self.level1.name})"
    
    class Meta:
        db_table = 'tb_requirement_level3'
    
    def as_dict(self):
        return {"id": self.id, "level1": self.level1.as_dict(), "level2": self.level2.as_dict(), "name": self.name}

class ChecklistQuestion(models.Model):
    REQUIREMENT_TYPE_CHOICES = [
        ('level1', 'Requirement Level 1'),
        ('level2', 'Requirement Level 2'),
        ('level3', 'Requirement Level 3')
    ]
    
    requirement_type = models.CharField(max_length=10, choices=REQUIREMENT_TYPE_CHOICES, verbose_name="Requirement Type")
    requirement_level1 = models.ForeignKey('RequirementLevel1', on_delete=models.PROTECT, null=True, blank=True, verbose_name="Requirement Level 1")
    requirement_level2 = models.ForeignKey('RequirementLevel2', on_delete=models.PROTECT, null=True, blank=True, verbose_name="Requirement Level 2")
    requirement_level3 = models.ForeignKey('RequirementLevel3', on_delete=models.PROTECT, null=True, blank=True, verbose_name="Requirement Level 3")
    question_text = models.CharField(max_length=500, verbose_name="Question Text")
    order = models.IntegerField(verbose_name="Order")
    
    def __str__(self):
        return self.question_text
    
    class Meta:
        db_table = 'tb_checklist_question'
    
    def as_dict(self):
        return {
            "id": self.id,
            "requirement_type": self.requirement_type,
            "requirement": self.get_selected_requirement(),
            "question_text": self.question_text,
            "order": self.order,
        }
    
    def get_selected_requirement(self):
        if self.requirement_type == 'level1':
            return self.requirement_level1.as_dict() if self.requirement_level1 else None
        elif self.requirement_type == 'level2':
            return self.requirement_level2.as_dict() if self.requirement_level2 else None
        elif self.requirement_type == 'level3':
            return self.requirement_level3.as_dict() if self.requirement_level3 else None
        return None

class Audited(models.Model):
    requirement_level1 = models.ForeignKey(RequirementLevel1, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Requirement Level 1")
    requirement_level2 = models.ForeignKey(RequirementLevel2, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Requirement Level 2")
    requirement_level3 = models.ForeignKey(RequirementLevel3, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Requirement Level 3")
    audited_person = models.ForeignKey(Person, on_delete=models.PROTECT, related_name="audited", verbose_name="Audited Person")

    def __str__(self):
        return f"{self.audited_person.first_name} {self.audited_person.last_name}"

    class Meta:
        db_table = 'tb_audited'

    def as_dict(self):
        return {
            "id": self.id,
            "requirement": self.get_selected_requirement(),
            "audited_person": self.audited_person.as_dict(),
        }

    def get_selected_requirement(self):
        if self.requirement_level1:
            return self.requirement_level1.as_dict()
        elif self.requirement_level2:
            return self.requirement_level2.as_dict()
        elif self.requirement_level3:
            return self.requirement_level3.as_dict()
        return None

class AuditedEvaluationQuestion(models.Model):
    audited = models.ForeignKey(Audited, on_delete=models.PROTECT, related_name="audited_questions", verbose_name="Audited")
    question_text = models.CharField(max_length=500, verbose_name="Question Text")
    order = models.IntegerField(verbose_name="Order")

    def __str__(self):
        return self.question_text

    class Meta:
        db_table = 'tb_audited_evaluation_question'

    def as_dict(self):
        return {
            "id": self.id,
            "audited": self.audited.as_dict(),
            "question_text": self.question_text,
            "order": self.order,
        }

class LeadAuditorEvaluationQuestion(models.Model):
    audited = models.ForeignKey(Audited, on_delete=models.PROTECT, related_name="lead_auditor_questions", verbose_name="Audited")
    question_text = models.CharField(max_length=500, verbose_name="Question Text")
    order = models.IntegerField(verbose_name="Order")

    def __str__(self):
        return self.question_text

    class Meta:
        db_table = 'tb_lead_auditor_evaluation_question'

    def as_dict(self):
        return {
            "id": self.id,
            "audited": self.audited.as_dict(),
            "question_text": self.question_text,
            "order": self.order,
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
    requirement_level1 = models.ForeignKey(RequirementLevel1, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Requirement Level 1")
    requirement_level2 = models.ForeignKey(RequirementLevel2, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Requirement Level 2")
    requirement_level3 = models.ForeignKey(RequirementLevel3, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Requirement Level 3")
    month = models.IntegerField(verbose_name="Month")
    year = models.IntegerField(verbose_name="Year")

    def __str__(self):
        return f"{self.get_selected_requirement()} - {self.month}/{self.year}"

    class Meta:
        db_table = 'tb_annual_program'

    def as_dict(self):
        return {
            "id": self.id,
            "requirement": self.get_selected_requirement(),
            "month": self.month,
            "year": self.year,
        }

    def get_selected_requirement(self):
        if self.requirement_level1:
            return self.requirement_level1.as_dict()
        elif self.requirement_level2:
            return self.requirement_level2.as_dict()
        elif self.requirement_level3:
            return self.requirement_level3.as_dict()
        return None

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
    requirement_level1 = models.ForeignKey(RequirementLevel1, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Requirement Level 1")
    requirement_level2 = models.ForeignKey(RequirementLevel2, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Requirement Level 2")
    requirement_level3 = models.ForeignKey(RequirementLevel3, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Requirement Level 3")
    audit_date = models.DateField(verbose_name="Audit Date")
    audit_time = models.CharField(max_length=50, verbose_name="Audit Time")
    audit_team_member = models.ForeignKey(AuditTeam, on_delete=models.PROTECT, verbose_name="Audit Team Member")
    audit_location = models.CharField(max_length=200, verbose_name="Audit Location")

    def __str__(self):
        return f"{self.get_selected_requirement()} - {self.audit_date} at {self.audit_time}"

    class Meta:
        db_table = 'tb_associated_elements'

    def as_dict(self):
        return {
            "id": self.id,
            "requirement": self.get_selected_requirement(),
            "audit_date": self.audit_date,
            "audit_time": self.audit_time,
            "audit_team_member": self.audit_team_member.as_dict(),
            "audit_location": self.audit_location,
        }

    def get_selected_requirement(self):
        if self.requirement_level1:
            return self.requirement_level1.as_dict()
        elif self.requirement_level2:
            return self.requirement_level2.as_dict()
        elif self.requirement_level3:
            return self.requirement_level3.as_dict()
        return None

class Checklist(models.Model):
    requirement_level1 = models.ForeignKey(RequirementLevel1, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Requirement Level 1")
    requirement_level2 = models.ForeignKey(RequirementLevel2, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Requirement Level 2")
    requirement_level3 = models.ForeignKey(RequirementLevel3, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Requirement Level 3")
    objective_evidence = models.TextField(verbose_name="Objective Evidence")
    compliance = models.TextField(verbose_name="Compliance")

    def __str__(self):
        return f"Checklist for {self.get_selected_requirement()}"

    class Meta:
        db_table = 'tb_checklist'

    def as_dict(self):
        return {
            "id": self.id,
            "requirement": self.get_selected_requirement(),
            "objective_evidence": self.objective_evidence,
            "compliance": self.compliance,
        }

    def get_selected_requirement(self):
        if self.requirement_level1:
            return self.requirement_level1.as_dict()
        elif self.requirement_level2:
            return self.requirement_level2.as_dict()
        elif self.requirement_level3:
            return self.requirement_level3.as_dict()
        return None

class AuditorEvaluation(models.Model):
    audited = models.ForeignKey(Audited, on_delete=models.PROTECT, related_name="auditor_evaluations", verbose_name="Audited")
    evaluation_date = models.DateField(verbose_name="Evaluation Date")

    def __str__(self):
        return f"Evaluation for {self.audited.audited_person.first_name} {self.audited.audited_person.last_name}"

    class Meta:
        db_table = 'tb_auditor_evaluation'

    def as_dict(self):
        return {
            "id": self.id,
            "audited": self.audited.as_dict(),
            "evaluation_date": self.evaluation_date,
        }

class FindingClassification(models.Model):
    CLASSIFICATION_CHOICES = [
        ('minor_non_conformity', 'Minor Non-Conformity'),
        ('major_non_conformity', 'Major Non-Conformity'),
        ('improvement_opportunity', 'Improvement Opportunity'),
    ]

    classification = models.CharField(max_length=50, choices=CLASSIFICATION_CHOICES, verbose_name="Classification")

    def __str__(self):
        return self.get_classification_display()

    class Meta:
        db_table = 'tb_finding_classification'

    def as_dict(self):
        return {
            "id": self.id,
            "classification": self.get_classification_display(),
        }

class Findings(models.Model):
    requirement_level1 = models.ForeignKey(RequirementLevel1, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Requirement Level 1")
    requirement_level2 = models.ForeignKey(RequirementLevel2, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Requirement Level 2")
    requirement_level3 = models.ForeignKey(RequirementLevel3, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Requirement Level 3")
    finding_text = models.TextField(verbose_name="Finding")
    classification = models.ForeignKey(FindingClassification, on_delete=models.PROTECT, verbose_name="Finding Classification")

    def __str__(self):
        return self.finding_text[:50]  

    class Meta:
        db_table = 'tb_findings'

    def as_dict(self):
        return {
            "id": self.id,
            "requirement": self.get_selected_requirement(),
            "finding_text": self.finding_text,
            "classification": self.classification.as_dict(),
        }

    def get_selected_requirement(self):
        if self.requirement_level1:
            return self.requirement_level1.as_dict()
        elif self.requirement_level2:
            return self.requirement_level2.as_dict()
        elif self.requirement_level3:
            return self.requirement_level3.as_dict()
        return None

class AuditReport(models.Model):
    summary = models.TextField(verbose_name="Summary of Audit Development")
    strengths = models.TextField(verbose_name="Strengths")

    def __str__(self):
        return self.summary[:50]  

    class Meta:
        db_table = 'tb_audit_report'

    def as_dict(self):
        return {
            "id": self.id,
            "summary": self.summary,
            "strengths": self.strengths,
        }



