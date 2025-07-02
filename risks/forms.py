from django import forms
from django.contrib.auth.models import User
from company.models import Position
from .models import (
    RiskIdentification, RiskEvaluation, RiskTreatment,
    ContingencyPlan, Reevaluation
)

class RiskIdentificationForm(forms.ModelForm):
    class Meta:
        model = RiskIdentification
        fields = ['area', 'process', 'identified_risk', 'consequences', 'source']
        widgets = {
            'area': forms.Select(attrs={'class': 'form-control'}),
            'process': forms.Select(attrs={'class': 'form-control'}), 
            'identified_risk': forms.TextInput(attrs={'class': 'form-control'}),
            'consequences': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'source': forms.TextInput(attrs={'class': 'form-control'}),
        }


class RiskEvaluationForm(forms.ModelForm):
    class Meta:
        model = RiskEvaluation
        fields = [
            'risk', 
            'severity',
            'current_preventive_controls',
            'occurrence',
            'current_detection_controls',
            'detection',
            'risk_level',
        ]
        widgets = {
            'risk': forms.Select(attrs={'class': 'form-select'}),
            'severity': forms.Select(attrs={'class': 'form-select'}),
            'occurrence': forms.Select(attrs={'class': 'form-select'}),
            'detection': forms.Select(attrs={'class': 'form-select'}),
            'current_preventive_controls': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'current_detection_controls': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'risk_level': forms.Select(attrs={'class': 'form-select'}),
        }

class RiskTreatmentForm(forms.ModelForm):
    responsible = forms.ModelMultipleChoiceField(
        queryset=Position.objects.all(),
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select',
            'data-choices': '',
            'data-choices-removeItem': '',
            'multiple': True,
        }),
        label="Responsible Position"
    )

    class Meta:
        model = RiskTreatment
        fields = ['risk', 'treatment_action', 'responsible', 'target_date', 'actual_date']
        widgets = {
            'risk': forms.Select(attrs={'class': 'form-select'}),
            'treatment_action': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'target_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'actual_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }


class ContingencyPlanForm(forms.ModelForm):
    contingency_actions = forms.MultipleChoiceField(
        choices=ContingencyPlan.ACTION_CHOICES,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select',
            'data-choices': '',
            'data-choices-removeItem': '',
            'multiple': True,
        }),
        label="Contingency Actions"
    )

    responsible = forms.ModelMultipleChoiceField(
        queryset=Position.objects.all(),
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select',
            'data-choices': '',
            'data-choices-removeItem': '',
            'multiple': True,
        }),
        label="Responsible Position(s)",
        required=False
    )

    communicate_to = forms.ModelMultipleChoiceField(
        queryset=Position.objects.all(),
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select',
            'data-choices': '',
            'data-choices-removeItem': '',
            'multiple': True,
        }),
        label="Communicate To Position(s)",
        required=False
    )

    class Meta:
        model = ContingencyPlan
        fields = ['risk', 'contingency_actions', 'responsible', 'communicate_to']
        widgets = {
            'risk': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['responsible'].initial = self.instance.responsible.all()
            self.fields['communicate_to'].initial = self.instance.communicate_to.all()

    def save(self, commit=True):
        instance = super().save(commit=commit)

        if commit:
            instance.responsible.clear()
            instance.communicate_to.clear()

            for position in self.cleaned_data.get('responsible', []):
                ContingencyPlanResponsible.objects.create(contingencyplan=instance, position=position)

            for position in self.cleaned_data.get('communicate_to', []):
                ContingencyPlanCommunicateTo.objects.create(contingencyplan=instance, position=position)

        return instance

class ReevaluationForm(forms.ModelForm):
    class Meta:
        model = Reevaluation
        fields = ['risk', 'severity', 'occurrence', 'detection', 'risk_level']
        widgets = {
            'risk': forms.Select(attrs={'class': 'form-select'}),
            'severity': forms.Select(attrs={'class': 'form-select'}),
            'occurrence': forms.Select(attrs={'class': 'form-select'}),
            'detection': forms.Select(attrs={'class': 'form-select'}),
            'risk_level': forms.Select(attrs={'class': 'form-select'}),
        }
