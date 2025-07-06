from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from .models import Expense
from .forms import ExpenseForm, RegisterForm
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from decimal import Decimal 
from scipy.stats import zscore
import numpy as np
import pandas as pd
import json
import joblib
import os

# Load the model once
model_path = os.path.join(os.path.dirname(__file__), 'expense_classifier.pkl')
expense_model = joblib.load(model_path)


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'tracker/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'tracker/login.html', {'form': form})


from .forms import IncomeForm

@login_required
def dashboard(request):
    expenses = Expense.objects.filter(user=request.user).order_by('-date', '-amount')
    total_expense = expenses.aggregate(Sum('amount'))['amount__sum'] or 0

    # Get or create income object
    income_obj, created = Income.objects.get_or_create(user=request.user, defaults={'amount': 0})

    # Handle income update form
    if request.method == 'POST' and 'update_income' in request.POST:
        income_form = IncomeForm(request.POST, instance=income_obj)
        if income_form.is_valid():
            income = income_form.save(commit=False)
            income.user = request.user
            income.save()
            return redirect('dashboard')
    else:
        income_form = IncomeForm(instance=income_obj)

    # Anomaly Detection (Weekly IQR based)
    anomaly_alert = None
    df_data = list(expenses.values('category', 'amount', 'date'))
    if df_data:
        df = pd.DataFrame(df_data)
        df['amount'] = df['amount'].astype(float)
        df['date'] = pd.to_datetime(df['date'])
        df['week'] = df['date'].dt.to_period('W').apply(lambda r: r.start_time)

        grouped = df.groupby(['category', 'week'])['amount'].apply(list)

        for (category, week), amounts in grouped.items():
            if len(amounts) > 2:
                q1 = np.percentile(amounts, 25)
                q3 = np.percentile(amounts, 75)
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr

                for amt in amounts:
                    if amt < lower_bound or amt > upper_bound:
                        anomaly_alert = f"⚠️ Unusual spending detected in '{category}' during week starting {week.date()}!"
                        break
            if anomaly_alert:
                break

    # Remaining income calculation
    income = income_obj.amount or 0
    remaining_income = float(income) - float(total_expense)
    warning = remaining_income < 500  # Customize warning threshold

    # Chart data
    dates = [expense.date.strftime("%Y-%m-%d") for expense in expenses]
    amounts = [float(expense.amount) for expense in expenses]

    context = {
        "expenses": expenses,
        "total_expense": total_expense,
        "dates": json.dumps(dates),
        "amounts": json.dumps(amounts),
        "remaining_income": remaining_income,
        "warning": warning,
        "income_form": income_form,
        "anomaly_alert": anomaly_alert,
    }
    return render(request, "tracker/dashboard.html", context)


@login_required
def add_expense(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
           
            # Predict category using model
            # if not expense.category:  # Only auto-detect if not selected
            #     predicted_category = expense_model.predict([expense.name])[0]
            #     expense.category = predicted_category
            expense.save()
            return redirect('dashboard')
    else:
        form = ExpenseForm()
    return render(request, 'tracker/add_expense.html', {'form': form})

@login_required
def delete_expense(request, expense_id):
    expense = Expense.objects.get(id=expense_id)
    if expense.user == request.user:
        expense.delete()
    return redirect('dashboard')

def user_logout(request):
    logout(request)
    return redirect('login')
from django.shortcuts import render, redirect, get_object_or_404
def update_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id, user=request.user)

    if request.method == "POST":
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            return redirect("dashboard")  # Redirect to dashboard after updating
    else:
        form = ExpenseForm(instance=expense)  # Pre-fill the form with existing data

    return render(request, "tracker/update_expense.html", {"form": form})
from .models import Income
from .forms import IncomeForm

@login_required
def set_income(request):
    try:
        income = Income.objects.get(user=request.user)
    except Income.DoesNotExist:
        income = None

    if request.method == 'POST':
        form = IncomeForm(request.POST, instance=income)
        if form.is_valid():
            new_income = form.save(commit=False)
            new_income.user = request.user
            new_income.save()
            return redirect('dashboard')
    else:
        form = IncomeForm(instance=income)

    return render(request, 'tracker/set_income.html', {'form': form})

# Create your views here.
