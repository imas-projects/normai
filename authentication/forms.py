from django import forms
from audits.models import Area
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm
'''
class UserSignUp(UserCreationForm):
    
    area = forms.ModelChoiceField(
        queryset=Area.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Select Area"
    )
    
    groups = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Select Group"
    )
    
    class Meta:
        model = User
        fields = ['first_name','last_name','username','email','groups','password' ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.TextInput(attrs={'class': 'form-control'}),
            'password': forms.PasswordInput(attrs={'class': 'form-control pe-5 password-input'}),
        }''
'''