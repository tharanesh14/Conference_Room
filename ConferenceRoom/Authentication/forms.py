from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User, Group
from django import forms

class CreateUserForm(UserCreationForm):
    user_group = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        empty_label="Select a user group",
        widget=forms.Select(attrs={'class': 'form-style'})
    )
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'user_group']
        
    def __init__(self, *args, **kwargs):
        super(CreateUserForm, self).__init__(*args, **kwargs)
        
        for field_name in self.fields:
            self.fields[field_name].widget.attrs['class'] = 'form-style'

class UserLoginForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username','password']
        widgets = {
            'username': forms.TextInput(attrs={'class':'form-style','placeholder':'User Name'}),
            'password': forms.PasswordInput(attrs={'class':'form-style','placeholder':'Password'}),
        }