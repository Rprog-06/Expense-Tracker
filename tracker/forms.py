from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Expense,Income

class ExpenseForm(forms.ModelForm):
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),  # Date picker input
        required=True
    )
    class Meta:
        model = Expense
        fields = ['name', 'amount','date']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

class RegisterForm(UserCreationForm):
    pass
class IncomeForm(forms.ModelForm):
    class Meta:
        model = Income
        fields = ['amount']
