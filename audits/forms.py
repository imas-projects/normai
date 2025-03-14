from django import forms
from .models import Person, AuditTeam, ChecklistQuestion, AuditedEvaluationQuestion, LeadAuditorEvaluationQuestion
from .models import AuditProgramHeader, AnnualProgram, AuditPlanHeader, Audited, AssociatedElements
from .models import Checklist, AuditorEvaluation, Findings, AuditReport

class PersonForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = ['first_name', 'last_name', 'parent_area', 'area', 'position']
        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': 'First Name', 'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Last Name', 'class': 'form-control'}),
            'parent_area': forms.Select(attrs={'class': 'form-control'}),
            'area': forms.Select(attrs={'class': 'form-control'}),
            'position': forms.Select(attrs={'class': 'form-control'}),
        }

class AuditTeamForm(forms.ModelForm):
    class Meta:
        model = AuditTeam
        fields = ['person', 'role']
        widgets = {
            'person': forms.Select(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
        }

class ChecklistQuestionForm(forms.ModelForm):
    class Meta:
        model = ChecklistQuestion
        fields = ['requirement_type', 'requirement_level1', 'requirement_level2', 'requirement_level3', 'question_text', 'order']
        widgets = {
            'requirement_type': forms.Select(attrs={'class': 'form-control'}),
            'requirement_level1': forms.Select(attrs={'class': 'form-control'}),
            'requirement_level2': forms.Select(attrs={'class': 'form-control'}),
            'requirement_level3': forms.Select(attrs={'class': 'form-control'}),
            'question_text': forms.Textarea(attrs={'placeholder': 'Enter question...', 'class': 'form-control', 'rows': 3}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class AuditedEvaluationQuestionForm(forms.ModelForm):
    class Meta:
        model = AuditedEvaluationQuestion
        fields = ['audited', 'question_text', 'order']
        widgets = {
            'audited': forms.Select(attrs={'class': 'form-control'}),
            'question_text': forms.Textarea(attrs={'placeholder': 'Enter question...', 'class': 'form-control', 'rows': 3}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class LeadAuditorEvaluationQuestionForm(forms.ModelForm):
    class Meta:
        model = LeadAuditorEvaluationQuestion
        fields = ['audited', 'question_text', 'order']
        widgets = {
            'audited': forms.Select(attrs={'class': 'form-control'}),
            'question_text': forms.Textarea(attrs={'placeholder': 'Enter question...', 'class': 'form-control', 'rows': 3}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class AuditProgramHeaderForm(forms.ModelForm):
    class Meta:
        model = AuditProgramHeader
        fields = ['objective', 'scope', 'audit_criteria', 'security_standards']
        widgets = {
            'objective': forms.Textarea(attrs={'placeholder': 'Enter objective...', 'class': 'form-control', 'rows': 3}),
            'scope': forms.Textarea(attrs={'placeholder': 'Enter scope...', 'class': 'form-control', 'rows': 3}),
            'audit_criteria': forms.Textarea(attrs={'placeholder': 'Enter audit criteria...', 'class': 'form-control', 'rows': 3}),
            'security_standards': forms.Textarea(attrs={'placeholder': 'Enter security standards...', 'class': 'form-control', 'rows': 3}),
        }

class AnnualProgramForm(forms.ModelForm):
    class Meta:
        model = AnnualProgram
        fields = ['requirement_level1', 'requirement_level2', 'requirement_level3', 'month', 'year']
        widgets = {
            'requirement_level1': forms.Select(attrs={'class': 'form-control'}),
            'requirement_level2': forms.Select(attrs={'class': 'form-control'}),
            'requirement_level3': forms.Select(attrs={'class': 'form-control'}),
            'month': forms.Select(attrs={'class': 'form-control', 'choices': [(i, i) for i in range(1, 13)]}),
            'year': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'YYYY'}),
        }

class AuditPlanHeaderForm(forms.ModelForm):
    class Meta:
        model = AuditPlanHeader
        fields = ['opening_meeting_location', 'opening_meeting_date_time', 'closing_meeting_location', 'closing_meeting_date_time']
        widgets = {
            'opening_meeting_location': forms.TextInput(attrs={'placeholder': 'Location of opening meeting', 'class': 'form-control'}),
            'opening_meeting_date_time': forms.DateTimeInput(attrs={'class': 'form-control', 'placeholder': 'YYYY-MM-DD HH:MM'}),
            'closing_meeting_location': forms.TextInput(attrs={'placeholder': 'Location of closing meeting', 'class': 'form-control'}),
            'closing_meeting_date_time': forms.DateTimeInput(attrs={'class': 'form-control', 'placeholder': 'YYYY-MM-DD HH:MM'}),
        }

class AuditedForm(forms.ModelForm):
    class Meta:
        model = Audited
        fields = ['requirement_level1', 'requirement_level2', 'requirement_level3', 'audited_person']
        widgets = {
            'requirement_level1': forms.Select(attrs={'class': 'form-control'}),
            'requirement_level2': forms.Select(attrs={'class': 'form-control'}),
            'requirement_level3': forms.Select(attrs={'class': 'form-control'}),
            'audited_person': forms.Select(attrs={'class': 'form-control'}),
        }

class AssociatedElementsForm(forms.ModelForm):
    class Meta:
        model = AssociatedElements
        fields = ['requirement_level1', 'requirement_level2', 'requirement_level3', 'audit_date', 'audit_time', 'audit_team_member', 'audit_location']
        widgets = {
            'requirement_level1': forms.Select(attrs={'class': 'form-control'}),
            'requirement_level2': forms.Select(attrs={'class': 'form-control'}),
            'requirement_level3': forms.Select(attrs={'class': 'form-control'}),
            'audit_date': forms.DateInput(attrs={'class': 'form-control', 'placeholder': 'YYYY-MM-DD'}),
            'audit_time': forms.TimeInput(attrs={'class': 'form-control', 'placeholder': 'HH:MM'}),
            'audit_team_member': forms.Select(attrs={'class': 'form-control'}),
            'audit_location': forms.TextInput(attrs={'placeholder': 'Location of audit', 'class': 'form-control'}),
        }

class ChecklistForm(forms.ModelForm):
    class Meta:
        model = Checklist
        fields = ['requirement_level1', 'requirement_level2', 'requirement_level3', 'objective_evidence', 'compliance']
        widgets = {
            'requirement_level1': forms.Select(attrs={'class': 'form-control'}),
            'requirement_level2': forms.Select(attrs={'class': 'form-control'}),
            'requirement_level3': forms.Select(attrs={'class': 'form-control'}),
            'objective_evidence': forms.Textarea(attrs={'placeholder': 'Enter objective evidence...', 'class': 'form-control', 'rows': 3}),
            'compliance': forms.Textarea(attrs={'placeholder': 'Enter compliance details...', 'class': 'form-control', 'rows': 3}),
        }

class AuditorEvaluationForm(forms.ModelForm):
    class Meta:
        model = AuditorEvaluation
        fields = ['audited', 'evaluation_date']
        widgets = {
            'audited': forms.Select(attrs={'class': 'form-control'}),
            'evaluation_date': forms.DateInput(attrs={'class': 'form-control', 'placeholder': 'YYYY-MM-DD'}),
        }

class FindingsForm(forms.ModelForm):
    class Meta:
        model = Findings
        fields = ['requirement_level1', 'requirement_level2', 'requirement_level3', 'finding_text', 'classification']
        widgets = {
            'requirement_level1': forms.Select(attrs={'class': 'form-control'}),
            'requirement_level2': forms.Select(attrs={'class': 'form-control'}),
            'requirement_level3': forms.Select(attrs={'class': 'form-control'}),
            'finding_text': forms.Textarea(attrs={'placeholder': 'Describe the finding...', 'class': 'form-control', 'rows': 3}),
            'classification': forms.Select(attrs={'class': 'form-control'}),
        }

class AuditReportForm(forms.ModelForm):
    class Meta:
        model = AuditReport
        fields = ['summary', 'strengths']
        widgets = {
            'summary': forms.Textarea(attrs={'placeholder': 'Summary of the audit...', 'class': 'form-control', 'rows': 3}),
            'strengths': forms.Textarea(attrs={'placeholder': 'Strength
