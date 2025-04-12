from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from .models import Expense
from .forms import ExpenseForm, RegisterForm
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from decimal import Decimal 
import json

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

@login_required
def dashboard(request):
    expenses = Expense.objects.filter(user=request.user).order_by('-date','-amount')
    total_expense =expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    expenses_by_date = Expense.objects.filter(user=request.user).values('date').annotate(total=Sum('amount')).order_by('date')

   
    # Prepare data for Chart.js
    dates = [expense.date.strftime("%Y-%m-%d") for expense in expenses]
    amounts = [float(expense.amount) for expense in expenses]
    context = {
        "expenses": expenses,
        "total_expense": sum(amounts),
        "dates": json.dumps(dates),  # Convert to JSON format for JavaScript
        "amounts": json.dumps(amounts),  # Convert to JSON format
    }
    return render(request, "tracker/dashboard.html", context)

@login_required
def add_expense(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
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

# Create your views here.
