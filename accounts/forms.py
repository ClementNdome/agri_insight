from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


class SignupForm(UserCreationForm):
    """Custom signup form with agriculture-specific fields"""
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email address'})
    )
    crop_interests = forms.MultipleChoiceField(
        required=False,
        choices=User.CROP_INTERESTS,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        help_text="Select crops you're interested in monitoring"
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'crop_interests', 'is_farmer')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
            'is_farmer': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirm Password'})
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        crop_interests = self.cleaned_data.get('crop_interests', [])
        if crop_interests:
            user.crop_interests = ','.join(crop_interests)
        if commit:
            user.save()
        return user

