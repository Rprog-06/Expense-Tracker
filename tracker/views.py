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
import re
import google.generativeai as genai
from django.conf import settings

def gemini_predict_category(expense_name):
    """
    Predicts expense category using Gemini API.
    Ensures flexible parsing and more accurate matching.
    """
    try:
        print("DEBUG: GEMINI_API_KEY =", os.getenv("GEMINI_API_KEY"))
        genai.configure(api_key=settings.GEMINI_API_KEY)
        

        model = genai.GenerativeModel("gemini-2.5-flash")

        prompt = f"""
        Categorize the following expense into one of these categories ONLY:
        [Food, Transport, Entertainment, Shopping, Bills, Health, Other]

        Expense: "{expense_name}"

        Output just ONE word — the category name exactly as listed above.
        """

        response = model.generate_content(prompt)
        text = response.text.strip()

        # ✅ Normalize and clean output
        text = re.sub(r'[^a-zA-Z]', '', text).capitalize()

        valid_categories = [
            "Food", "Transport", "Entertainment", "Shopping", "Bills", "Health", "Other"
        ]

        # ✅ Fuzzy correction: handle small differences (e.g., "Foods", "Transporting")
        for category in valid_categories:
            if category.lower() in text.lower():
                return category

        print(f"[⚠️ Gemini Output Unrecognized] Got: {text}")
        return "Other"

    except Exception as e:
        print("Gemini Error:", e)
        return "Other"



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
    try:
        print("⚙️ Loading dashboard for:", request.user)

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

        # 1️⃣ Check database connectivity and Income table existence
        try:
            expenses = Expense.objects.filter(user=request.user).order_by('-date', '-amount')
        except Exception as e:
            print("🔥 Expense table error:", e)
            context["error"] = f"Expense DB error: {e}"
            return render(request, "tracker/dashboard.html", context)

        context["expenses"] = expenses
        total_expense = float(expenses.aggregate(Sum('amount'))['amount__sum'] or 0)
        context["total_expense"] = total_expense

        # 2️⃣ Check Income table
        try:
            income_obj, created = Income.objects.get_or_create(user=request.user, defaults={'amount': Decimal('0')})
            income = float(income_obj.amount or 0)
            context["remaining_income"] = income - total_expense
            context["warning"] = context["remaining_income"] < 500
        except Exception as e:
            print("🔥 Income table error:", e)
            context["error"] = f"Income DB error: {e}"
            return render(request, "tracker/dashboard.html", context)

        # 3️⃣ Load income form safely
        try:
            if request.method == 'POST' and 'update_income' in request.POST:
                income_form = IncomeForm(request.POST, instance=income_obj)
                if income_form.is_valid():
                    income_form.save()
                    return redirect('dashboard')
            else:
                income_form = IncomeForm(instance=income_obj)
            context["income_form"] = income_form
        except Exception as e:
            print("🔥 IncomeForm error:", e)
            context["error"] = "Could not load income form."

        # 4️⃣ Prepare chart data safely
        try:
            dates = [e.date.strftime("%Y-%m-%d") for e in expenses]
            amounts = [float(e.amount) for e in expenses]
            context["dates"] = json.dumps(dates)
            context["amounts"] = json.dumps(amounts)
        except Exception as e:
            print("🔥 Chart data error:", e)
            context["error"] = "Chart data generation failed."

        return render(request, "tracker/dashboard.html", context)

    except Exception as e:
        print("🔥 Dashboard crashed:", e)
        return render(request, "tracker/dashboard.html", {"error": f"Critical: {e}"})

        
@login_required
def add_expense(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            
            # If category is empty or "Other", try to predict it
            if not expense.category or expense.category == 'Other':
                expense.category = gemini_predict_category(expense.name)
               
            
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