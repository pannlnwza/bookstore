from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Review

class SignUpForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Password")
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean_confirm_password(self):
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')

        if password != confirm_password:
            raise ValidationError("Passwords do not match.")
        return confirm_password

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Email is already in use.")
        return email


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['name', 'review_message', 'rating']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Name or alias', 'max_length': 50}),
            'review_message': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Write your review...'}),
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 5}),
        }
        labels = {
            'name': 'Name',
            'review_message': 'Review',
            'rating': 'Rating (1-5)',
        }