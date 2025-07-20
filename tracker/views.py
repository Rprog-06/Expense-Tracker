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

from django.conf import settings




# Add this to your views.py
KEYWORD_MAPPING = {
    # Bills/Utilities
    'electricity': 'Bills',
    'bill': 'Bills',
    'internet': 'Bills',
    'water': 'Bills',
    
    # Travel
    'bus': 'Travel',
    'uber': 'Travel',
    'lyft': 'Travel',
    'taxi': 'Travel',
    'fuel': 'Travel',
    'gas': 'Travel',
    'ticket': 'Travel',
    
    # Shopping
    'shirt': 'Shopping',
    't-shirt': 'Shopping',
    'jeans': 'Shopping',
    'store': 'Shopping',
    'mall': 'Shopping',
    
    # Entertainment
    'movie': 'Entertainment',
    'netflix': 'Entertainment',
    'concert': 'Entertainment',
    
    # Food
    'restaurant': 'Food',
    'grocer': 'Food',
    'dinner': 'Food',
    'lunch': 'Food',
    'coffee': 'Food',
    'jalebi': 'Food',
    'burger': 'Food'
}

def predict_category(expense_name):
    expense_lower = expense_name.lower()
    
    # 1. First check keyword mapping
    for keyword, category in KEYWORD_MAPPING.items():
        if keyword in expense_lower:
            return category
    
    # 2. Try local model (if exists)
    try:
        if 'expense_model' in globals():
            predicted = expense_model.predict([expense_name])[0]
            if predicted in STANDARD_CATEGORIES:
                return predicted
    except:
        pass
    
    # 3. Final fallback
    return 'Other'







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
@login_required
def dashboard(request):
    try:
        # Initialize context with safe defaults
        context = {
            "expenses": [],
            "total_expense": 0,
            "dates": json.dumps([]),
            "amounts": json.dumps([]),
            "remaining_income": 0,
            "warning": False,
            "income_form": None,
            "anomaly_alerts": [],
            "error": None
        }

        # 1. Get and process expenses
        expenses = Expense.objects.filter(user=request.user).order_by('-date', '-amount')
        context["expenses"] = expenses
        
        # Calculate totals (handling Decimal properly)
        total_expense = float(expenses.aggregate(Sum('amount'))['amount__sum']) or 0.0
        context["total_expense"] = total_expense
        
        # 2. Handle income
        income_obj, created = Income.objects.get_or_create(user=request.user, defaults={'amount': Decimal('0')})
        income = float(income_obj.amount) if income_obj.amount else 0.0
        context["remaining_income"] = income - total_expense
        context["warning"] = context["remaining_income"] < 500

        # Income form handling
        if request.method == 'POST' and 'update_income' in request.POST:
            income_form = IncomeForm(request.POST, instance=income_obj)
            if income_form.is_valid():
                income_form.save()
                return redirect('dashboard')
        else:
            income_form = IncomeForm(instance=income_obj)
        context["income_form"] = income_form

        # 3. Enhanced Anomaly Detection System
        if expenses.exists():
            try:
                # Prepare dataframe with proper decimal conversion
                df = pd.DataFrame(list(expenses.values('id', 'name', 'category', 'amount', 'date')))
                df['amount'] = df['amount'].apply(lambda x: float(x))  # Convert all to float
                df['date'] = pd.to_datetime(df['date'], errors='coerce')
                df = df.dropna()
                
                if not df.empty:
                    alerts = []
                    median_amount = float(df['amount'].median())
                    
                    # Detection 1: Absolute large expenses (2.5x median or ₹2000+)
                    large_threshold = max(2000, median_amount * 2.5)
                    large_expenses = df[df['amount'] > large_threshold]
                    for _, row in large_expenses.iterrows():
                        alerts.append(
                            f"⚠️ Large Expense: ₹{row['amount']:.2f} for {row['name']} "
                            f"(exceeds ₹{large_threshold:.2f} threshold)"
                        )
                    
                    # Detection 2: Weekly bill clusters (3+ bills/week)
                    bills = df[df['category'].str.lower().str.contains('bill')]
                    if not bills.empty:
                        bills['week'] = bills['date'].dt.to_period('W').apply(lambda r: r.start_time)
                        weekly_bills = bills.groupby('week').agg(
                            count=('amount', 'count'),
                            total=('amount', 'sum')
                        ).reset_index()
                        
                        for _, row in weekly_bills[weekly_bills['count'] >= 2].iterrows():
                            alerts.append(
                                f"⚠️ Bill Cluster: {row['count']} bills totaling "
                                f"₹{row['total']:.2f} (week of {row['week'].strftime('%m/%d')})"
                            )
                    
                    # Detection 3: Category anomalies (IQR method)
                    df['week'] = df['date'].dt.to_period('W')
                    for (category, week), group in df.groupby(['category', 'week']):
                        if len(group) > 1:
                            amounts = group['amount'].values.astype(float)
                            q1, q3 = np.percentile(amounts, [25, 75])
                            iqr = q3 - q1
                            lower, upper = q1 - 1.5*iqr, q3 + 1.5*iqr
                            
                            anomalies = group[(group['amount'] < lower) | (group['amount'] > upper)]
                            for _, row in anomalies.iterrows():
                                alerts.append(
                                    f"⚠️ Unusual {category} spending: ₹{row['amount']:.2f} "
                                    f"(typical range: ₹{lower:.2f}-₹{upper:.2f})"
                                )
                    
                    context["anomaly_alerts"] = alerts[:5]  # Show max 5 alerts

            except Exception as e:
                print(f"Anomaly detection error: {str(e)}")
                context["error"] = "Could not analyze spending patterns"

        # 4. Prepare chart data with proper decimal handling
        try:
            dates = [e.date.strftime("%Y-%m-%d") for e in expenses]
            amounts = [float(e.amount) for e in expenses]  # Convert Decimal to float
            context["dates"] = json.dumps(dates)
            context["amounts"] = json.dumps(amounts)
        except Exception as e:
            print(f"Chart data error: {str(e)}")
            context["error"] = "Could not prepare chart data"

        return render(request, "tracker/dashboard.html", context)

    except Exception as e:
        print(f"Dashboard error: {str(e)}")
        context["error"] = "System error loading dashboard"
        return render(request, "tracker/dashboard.html", context)
@login_required
def add_expense(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            
            # If category is empty or "Other", try to predict it
            if not expense.category or expense.category == 'Other':
                expense.category = predict_category(expense.name)
               
            
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
@login_required
def recategorize(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id, user=request.user)
    
    if request.method == 'POST':
        new_category = request.POST.get('category')
        if new_category in STANDARD_CATEGORIES:
            expense.category = new_category
            expense.save()
            return redirect('dashboard')
    
    return render(request, 'tracker/recategorize.html', {
        'expense': expense,
        'categories': STANDARD_CATEGORIES
    })