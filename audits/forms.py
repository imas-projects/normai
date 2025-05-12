from django import forms
from django.contrib.auth.models import User
from .models import (
    AuditProgramHeader, AnnualProgram, AuditPlanHeader,
    Audited, AssociatedElements, Checklist, Findings, AuditReport,
    Requirement, Area
)


class AuditProgramHeaderForm(forms.ModelForm):
    class Meta:
        model = AuditProgramHeader
        fields = ['objective', 'scope', 'audit_criteria', 'security_standards', 'start_date', 'end_date']
        widgets = {
            'objective': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'scope': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'audit_criteria': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'security_standards': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class AuditPlanHeaderForm(forms.ModelForm):
    class Meta:
        model = AuditPlanHeader
        fields = [
            'opening_meeting_location', 'opening_meeting_date_time',
            'closing_meeting_location', 'closing_meeting_date_time',
            'reviewed_by', 'approved_by'
        ]
        widgets = {
            'opening_meeting_location': forms.TextInput(attrs={'class': 'form-control'}),
            'opening_meeting_date_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'closing_meeting_location': forms.TextInput(attrs={'class': 'form-control'}),
            'closing_meeting_date_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'reviewed_by': forms.Select(attrs={'class': 'form-control'}),
            'approved_by': forms.Select(attrs={'class': 'form-control'}),
        }


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
    class Meta:
        model = AssociatedElements
        fields = ['requirement', 'audit_date', 'audit_time', 'audit_location']
        widgets = {
            'requirement': forms.Select(attrs={'class': 'form-control'}),
            'audit_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'audit_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'audit_location': forms.TextInput(attrs={'placeholder': 'Location of audit', 'class': 'form-control'}),
        }


class ChecklistForm(forms.ModelForm):
    class Meta:
        model = Checklist
        fields = ['requirement', 'question_text', 'order', 'objective_evidence', 'compliance', 'rating']
        widgets = {
            'requirement': forms.Select(attrs={'class': 'form-control'}),
            'question_text': forms.Textarea(attrs={'placeholder': 'Enter question...', 'class': 'form-control', 'rows': 3}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'objective_evidence': forms.Textarea(attrs={'placeholder': 'Enter objective evidence...', 'class': 'form-control', 'rows': 3}),
            'compliance': forms.Textarea(attrs={'placeholder': 'Enter compliance details...', 'class': 'form-control', 'rows': 3}),
            'rating': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Rating'}),
        }


class FindingsForm(forms.ModelForm):
    class Meta:
        model = Findings
        fields = ['requirement', 'finding_text', 'classification', 'corrective_action', 'root_cause']
        widgets = {
            'requirement': forms.Select(attrs={'class': 'form-control'}),
            'finding_text': forms.Textarea(attrs={'placeholder': 'Describe the finding...', 'class': 'form-control', 'rows': 3}),
            'classification': forms.Select(attrs={'class': 'form-control'}),
            'corrective_action': forms.Textarea(attrs={'placeholder': 'Corrective action...', 'class': 'form-control', 'rows': 3}),
            'root_cause': forms.Textarea(attrs={'placeholder': 'Root cause...', 'class': 'form-control', 'rows': 3}),
        }


class AuditReportForm(forms.ModelForm):
    class Meta:
        model = AuditReport
        fields = ['requirement', 'summary', 'strengths', 'opportunities_for_improvement', 'nonconformities']
        widgets = {
            'requirement': forms.Select(attrs={'class': 'form-control'}),
            'summary': forms.Textarea(attrs={'placeholder': 'Summary of the audit...', 'class': 'form-control', 'rows': 3}),
            'strengths': forms.Textarea(attrs={'placeholder': 'Strengths...', 'class': 'form-control', 'rows': 3}),
            'opportunities_for_improvement': forms.Textarea(attrs={'placeholder': 'Opportunities for improvement...', 'class': 'form-control', 'rows': 3}),
            'nonconformities': forms.Textarea(attrs={'placeholder': 'Nonconformities...', 'class': 'form-control', 'rows': 3}),
        }


class RequirementChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        prefix = ""
        current = obj
        while current and current.parent:
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

    parent = RequirementChoiceField(
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

