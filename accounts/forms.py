from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.forms.utils import ErrorList
from django.utils.safestring import mark_safe
from django import forms
from .models import UserProfile

class CustomErrorList(ErrorList):
    def __str__(self):
        if not self:
            return ''
        return mark_safe(
            ''.join(
                [f'<div class="alert alert-danger" role="alert">{e}</div>' for e in self]
            )
        )

class LocationForm(forms.Form):
    state = forms.CharField(
        max_length=100, 
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., California, Texas, Florida'})
    )
    country = forms.CharField(
        max_length=100, 
        initial='United States',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

class CustomUserCreationForm(UserCreationForm):
    state = forms.CharField(
        max_length=100, 
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., California, Texas, Florida'})
    )
    country = forms.CharField(
        max_length=100, 
        initial='United States',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = User
        fields = ('username', 'password1', 'password2', 'state', 'country')
    
    def __init__(self, *args, **kwargs):
        super(CustomUserCreationForm, self).__init__(*args, **kwargs)
        for fieldname in ['username', 'password1', 'password2']:
            self.fields[fieldname].help_text = '' # Not typed as Optional
            self.fields[fieldname].widget.attrs.update( {'class': 'form-control'} )
    
    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            # Create or update the user profile with location data
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.state = self.cleaned_data['state']
            profile.country = self.cleaned_data['country']
            profile.save()
        return user