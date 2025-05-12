from django import forms
from .models import RiskIdentification, RiskEvaluation, RiskTreatment, ContingencyPlan, Reevaluation, Role
from company.models import Area

class RiskIdentificationForm(forms.ModelForm):
    class Meta:
        model = RiskIdentification
        fields = ['area', 'activity_name', 'identified_risk', 'consequences']
        widgets = {
            'area': forms.Select(attrs={'class': 'form-control'}),
            'activity_name': forms.TextInput(attrs={'class': 'form-control'}),
            'identified_risk': forms.TextInput(attrs={'class': 'form-control'}),
            'consequences': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

class RiskEvaluationForm(forms.ModelForm):
    risk = forms.ModelChoiceField(
        queryset=RiskIdentification.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Select Risk"
    )
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
            'severity': forms.Select(attrs={'class': 'form-select'}),
            'occurrence': forms.Select(attrs={'class': 'form-select'}),
            'detection': forms.Select(attrs={'class': 'form-select'}),
            'current_preventive_controls': forms.Textarea(attrs={'class': 'form-control'}),
            'current_detection_controls': forms.Textarea(attrs={'class': 'form-control'}),
            'risk_level': forms.Select(attrs={'class': 'form-select'}),
        }

class RiskTreatmentForm(forms.ModelForm):
    risk = forms.ModelChoiceField(
        queryset=RiskIdentification.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Select Risk"
    )
    responsible = forms.ModelMultipleChoiceField(
        queryset=Role.objects.all(),
        widget=forms.CheckboxSelectMultiple(), 
        label="Responsible"
    )

    class Meta:
        model = RiskTreatment
        fields = ['risk', 'treatment_action', 'responsible', 'target_date', 'actual_date']
        widgets = {
            'treatment_action': forms.TextInput(attrs={'class': 'form-control'}),
            'target_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'actual_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }


class ContingencyPlanForm(forms.ModelForm):
    risk = forms.ModelChoiceField(
        queryset=RiskIdentification.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Select Risk"
    )
    class Meta:
        model = ContingencyPlan
        fields = ['risk', 'contingency_actions', 'responsible', 'communicate_to']
        widgets = {
            'contingency_actions': forms.CheckboxSelectMultiple(),
            'responsible': forms.CheckboxSelectMultiple(),
            'communicate_to': forms.CheckboxSelectMultiple(),
        }

class ReevaluationForm(forms.ModelForm):
    risk = forms.ModelChoiceField(
        queryset=RiskIdentification.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Select Risk"
    )
    class Meta:
        model = Reevaluation
        fields = ['risk', 'severity', 'occurrence', 'detection', 'risk_level']
        widgets = {
            'severity': forms.Select(attrs={'class': 'form-select'}),
            'occurrence': forms.Select(attrs={'class': 'form-select'}),
            'detection': forms.Select(attrs={'class': 'form-select'}),
            'risk_level': forms.Select(attrs={'class': 'form-select'}),  
        }

