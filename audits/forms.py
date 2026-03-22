from django import forms
from django.contrib.auth.models import User
from .models import (
    AuditProgramHeader, AnnualProgram, AnnualPlan,
    AnnualPlanAuditor, AnnualPlanAudited, Checklist, Findings, AuditReport,
    ProcessRequirement, AuditedEvaluationQuestion, AuditorEvaluation, LeadAuditorEvaluationQuestion, CorrectiveAction, CorrectiveActionFollowUp
)

class AuditProgramHeaderForm(forms.ModelForm):
    class Meta:
        model = AuditProgramHeader
        fields = ['year', 'objective', 'scope', 'audit_criteria', 'security_standards']
        widgets = {
            'year': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'YYYY'}),
            'objective': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'scope': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'audit_criteria': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'security_standards': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class AnnualProgramForm(forms.ModelForm):
    class Meta:
        model = AnnualProgram
        fields = ['program_header', 'process', 'month']
        widgets = {
            'program_header': forms.Select(attrs={'class': 'form-control'}),
            'process': forms.Select(attrs={'class': 'form-control'}),
            'month': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 12, 'placeholder': 'Month (1-12)'}),
        }

class AnnualPlanForm(forms.ModelForm):
    class Meta:
        model = AnnualPlan
        fields = [
            'annual_program', 
            'audit_opening_date', 'audit_opening_time',
            'audit_opening_location', 'audit_closing_date',
            'audit_closing_time', 'audit_closing_location'
        ]
        widgets = {
            'annual_program': forms.Select(attrs={'class': 'form-control'}),
            'audit_opening_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'audit_opening_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'audit_opening_location': forms.TextInput(attrs={'class': 'form-control'}),
            'audit_closing_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'audit_closing_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'audit_closing_location': forms.TextInput(attrs={'class': 'form-control'}),
        }


class AnnualPlanAuditorForm(forms.ModelForm):
    class Meta:
        model = AnnualPlanAuditor
        fields = ['annual_plan', 'user']
        widgets = {
            'annual_plan': forms.Select(attrs={'class': 'form-control'}),
            'user': forms.Select(attrs={'class': 'form-control'}),
        }

class AnnualPlanAuditedForm(forms.ModelForm):
    class Meta:
        model = AnnualPlanAudited
        fields = ['annual_plan', 'user']
        widgets = {
            'annual_plan': forms.Select(attrs={'class': 'form-control'}),
            'user': forms.Select(attrs={'class': 'form-control'}),
        }

class ChecklistForm(forms.ModelForm):
    class Meta:
        model = Checklist
        fields = ['audit_plan', 'question', 'orden', 'compliance', 'evidence']
        widgets = {
            'audit_plan': forms.Select(attrs={'class': 'form-control'}),
            'question': forms.Select(attrs={'class': 'form-control'}),
            'orden': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'compliance': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'evidence': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class FindingsForm(forms.ModelForm):
    class Meta:
        model = Findings
        fields = ['audit_plan', 'requirement', 'finding_text', 'classification']
        widgets = {
            'audit_plan': forms.Select(attrs={'class': 'form-control'}),
            'requirement': forms.Select(attrs={'class': 'form-control'}),
            'finding_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'classification': forms.Select(attrs={'class': 'form-control'}),
        }


class AuditReportForm(forms.ModelForm):
    class Meta:
        model = AuditReport
        fields = ['audit_plan', 'summary', 'recommendations', 'conclusions']
        widgets = {
            'audit_plan': forms.Select(attrs={'class': 'form-control'}),
            'summary': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'recommendations': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'conclusions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class ProcessRequirementForm(forms.ModelForm):
    class Meta:
        model = ProcessRequirement
        fields = ['process', 'requirement']
        widgets = {
            'process': forms.Select(attrs={'class': 'form-control'}),
            'requirement': forms.Select(attrs={'class': 'form-control'}),
        }

class AuditedEvaluationQuestionForm(forms.ModelForm):
    class Meta:
        model = AuditedEvaluationQuestion
        fields = ['requirement', 'question_text']
        widgets = {
            'requirement': forms.Select(attrs={'class': 'form-control'}),
            'question_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class AuditorEvaluationForm(forms.ModelForm):
    class Meta:
        model = AuditorEvaluation
        fields = ['audit_plan', 'question', 'orden', 'rate']
        widgets = {
            'audit_plan': forms.Select(attrs={'class': 'form-control'}),
            'question': forms.Select(attrs={'class': 'form-control'}),
            'orden': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'rate': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 10}),
        }

class LeadAuditorEvaluationQuestionForm(forms.ModelForm):
    class Meta:
        model = LeadAuditorEvaluationQuestion
        fields = ['question_text', 'type']
        widgets = {
            'question_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'type': forms.Select(attrs={'class': 'form-control'}),
        }


class CorrectiveActionForm(forms.ModelForm):
    class Meta:
        model = CorrectiveAction
        fields = ['corrective_action', 'due_date', 'responsible_user', 'audit_report']
        widgets = {
            'corrective_action': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'responsible_user': forms.Select(attrs={'class': 'form-control'}),
            'audit_report': forms.Select(attrs={'class': 'form-control'}),
        }

class CorrectiveActionFollowUpForm(forms.ModelForm):
    class Meta:
        model = CorrectiveActionFollowUp
        fields = ['corrective_action', 'followup_date', 'status', 'comments']
        widgets = {
            'corrective_action': forms.Select(attrs={'class': 'form-control'}),
            'followup_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
