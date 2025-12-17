from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User


class LoginForm(AuthenticationForm):
    username = forms.CharField(max_length=100, label='Имя пользователя', widget=forms.TextInput(attrs={'class': 'form-input'}))
    password = forms.CharField(max_length=50, label='Пароль', widget=forms.PasswordInput(attrs={'class': 'form-input'}))
    # class Meta:
    #     model = User
    #     fields = ['username', 'password']


class RegisterForm(UserCreationForm):
    username = forms.CharField(max_length=100, label='Имя пользователя', widget=forms.TextInput(attrs={'class': 'form-input'}))
    password1 = forms.CharField(max_length=50, label='Пароль', widget=forms.PasswordInput(attrs={'class': 'form-input'}))
    password2 = forms.CharField(max_length=50, label='Повторите пароль', widget=forms.PasswordInput(attrs={'class': 'form-input'}))

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']

    # def clean_email(self):
    #     email = self.cleaned_data['email']
    #     if User.objects.filter(email=email).exists():
    #         raise forms.ValidationError('Пользователь с таким email уже существует')
    #     return email
