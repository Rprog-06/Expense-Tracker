from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Expense

class ExpenseForm(forms.ModelForm):
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),  # Date picker input
        required=True
    )
    class Meta:
        model = Expense
        fields = ['name', 'amount']

class RegisterForm(UserCreationForm):
    pass
