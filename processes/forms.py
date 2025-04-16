from django import forms
from .models import Process

class ProcessForm(forms.ModelForm):
    class Meta:
        model = Process
        fields = '__all__'
        widgets = {
            'creation_date': forms.DateInput(attrs={'type': 'date'}),
            'review_date': forms.DateInput(attrs={'type': 'date'}),
        }