from django import forms
from django.contrib.auth.models import User
from .models import AuditTeam, AuditedEvaluationQuestion, LeadAuditorEvaluationQuestion
from .models import AuditProgramHeader, AnnualProgram, AuditPlanHeader, Audited, AssociatedElements
from .models import Checklist, AuditorEvaluation, Findings, AuditReport, Requirement, Area


class AuditTeamForm(forms.ModelForm):
    person = forms.ModelChoiceField(
        queryset=User.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Auditor"
    )

    class Meta:
        model = AuditTeam
        fields = ['person', 'role']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-control'}),
        }


class AuditedEvaluationQuestionForm(forms.ModelForm):
    class Meta:
        model = AuditedEvaluationQuestion
        fields = ['requirement', 'question_text', 'order', 'rating']
        widgets = {
            'requirement': forms.Select(attrs={'class': 'form-control'}),
            'question_text': forms.Textarea(attrs={'placeholder': 'Enter question...', 'class': 'form-control', 'rows': 3}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'rating': forms.TextInput(attrs={'placeholder': 'Enter rating...', 'class': 'form-control'}),
        }


class LeadAuditorEvaluationQuestionForm(forms.ModelForm):
    class Meta:
        model = LeadAuditorEvaluationQuestion
        fields = ['requirement', 'question_text', 'order', 'rating']
        widgets = {
            'requirement': forms.Select(attrs={'class': 'form-control'}),
            'question_text': forms.Textarea(attrs={'placeholder': 'Enter question...', 'class': 'form-control', 'rows': 3}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'rating': forms.TextInput(attrs={'placeholder': 'Enter rating...', 'class': 'form-control'}),
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


class AuditPlanHeaderForm(forms.ModelForm):
    class Meta:
        model = AuditPlanHeader
        fields = ['opening_meeting_location', 'opening_meeting_date_time', 'closing_meeting_location', 'closing_meeting_date_time']
        widgets = {
            'opening_meeting_location': forms.TextInput(attrs={'placeholder': 'Location of opening meeting', 'class': 'form-control'}),
            'opening_meeting_date_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'closing_meeting_location': forms.TextInput(attrs={'placeholder': 'Location of closing meeting', 'class': 'form-control'}),
            'closing_meeting_date_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }


class AuditorEvaluationForm(forms.ModelForm):
    class Meta:
        model = AuditorEvaluation
        fields = ['requirement', 'evaluation_date']
        widgets = {
            'requirement': forms.Select(attrs={'class': 'form-control'}),
            'evaluation_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class AuditReportForm(forms.ModelForm):
    class Meta:
        model = AuditReport
        fields = ['requirement', 'summary', 'strengths']
        widgets = {
            'requirement': forms.Select(attrs={'class': 'form-control'}),
            'summary': forms.Textarea(attrs={'placeholder': 'Summary of the audit...', 'class': 'form-control', 'rows': 3}),
            'strengths': forms.Textarea(attrs={'placeholder': 'Strength', 'class': 'form-control', 'rows': 3}),
        }


class RequirementChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        prefix = ""
        current = obj
        while current:
            prefix += "-- "
            current = current.parent
        return f"{prefix}{obj.name}"


class UnifiedRequirementForm(forms.ModelForm):
    new_requirement_name = forms.CharField(
        max_length=200,
        required=True,
        label="New Requirement Name",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter new requirement...'})
    )

    parent = forms.ModelChoiceField(
        queryset=Requirement.objects.all(),
        required=False,
        label="Parent Requirement",
        widget=forms.Select(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = Requirement
        fields = ['new_requirement_name', 'parent']

    def save(self, commit=True):
        new_requirement = Requirement(
            name=self.cleaned_data['new_requirement_name'],
            parent=self.cleaned_data['parent']
        )
        if commit:
            new_requirement.save()
        return new_requirement


class AnnualProgramForm(forms.ModelForm):
    MONTH_CHOICES = [
        (1, "January"), (2, "February"), (3, "March"), (4, "April"),
        (5, "May"), (6, "June"), (7, "July"), (8, "August"),
        (9, "September"), (10, "October"), (11, "November"), (12, "December")
    ]

    month = forms.ChoiceField(choices=MONTH_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model = AnnualProgram
        fields = ['requirement', 'month', 'year']
        widgets = {
            'requirement': forms.Select(attrs={'class': 'form-control'}),
            'year': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'YYYY'}),
        }


class AuditedForm(forms.ModelForm):
    audited_user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Audited User"
    )

    class Meta:
        model = Audited
        fields = ['requirement', 'audited_user']
        widgets = {
            'requirement': forms.Select(attrs={'class': 'form-control'}),
        }


class AssociatedElementsForm(forms.ModelForm):
    audit_team_member = forms.ModelChoiceField(
        queryset=AuditTeam.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Audit Team Member"
    )

    class Meta:
        model = AssociatedElements
        fields = ['requirement', 'audit_date', 'audit_time', 'audit_team_member', 'audit_location']
        widgets = {
            'requirement': forms.Select(attrs={'class': 'form-control'}),
            'audit_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'audit_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'audit_location': forms.TextInput(attrs={'placeholder': 'Location of audit', 'class': 'form-control'}),
        }


class ChecklistForm(forms.ModelForm):
    class Meta:
        model = Checklist
        fields = ['requirement', 'question_text', 'order', 'objective_evidence', 'compliance']
        widgets = {
            'requirement': forms.Select(attrs={'class': 'form-control'}),
            'question_text': forms.Textarea(attrs={'placeholder': 'Enter question...', 'class': 'form-control', 'rows': 3}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'objective_evidence': forms.Textarea(attrs={'placeholder': 'Enter objective evidence...', 'class': 'form-control', 'rows': 3}),
            'compliance': forms.Textarea(attrs={'placeholder': 'Enter compliance details...', 'class': 'form-control', 'rows': 3}),
        }


class FindingsForm(forms.ModelForm):
    class Meta:
        model = Findings
        fields = ['requirement', 'finding_text', 'classification']
        widgets = {
            'requirement': forms.Select(attrs={'class': 'form-control'}),
            'finding_text': forms.Textarea(attrs={'placeholder': 'Describe the finding...', 'class': 'form-control', 'rows': 3}),
            'classification': forms.Select(choices=[(i, str(i)) for i in range(6)], attrs={'class': 'form-control'}),
        }
