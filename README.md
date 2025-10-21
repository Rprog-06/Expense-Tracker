# 💰 Expense Tracker with AI-Powered Anomaly Detection

A full-featured *Django-based Expense Tracker* that helps you manage your finances efficiently.  
It includes *AI category prediction (Gemini API), **anomaly detection, and a **Chart.js visualization dashboard* — all wrapped in a clean, responsive Bootstrap UI.

---

## 🚀 Features

✅ *Add, Edit & Delete Expenses*  
Easily manage all your daily expenses in one place.

✅ *Income Tracking*  
Set your total income and view your remaining balance in real-time.

✅ *AI-Powered Category Prediction*  
When you add an expense with an undefined category, *Gemini AI* automatically predicts the best matching category.

✅ *Smart Anomaly Detection*
Detects unusual spending patterns automatically:
- ⚠ *Large Expense Detection* — Finds unusually high expenses.
- ⚠ *Bill Cluster Detection* — Detects multiple bills in the same week.
- ⚠ *Category IQR Anomalies* — Identifies outliers within each category.

✅ *Dynamic Chart.js Visualization*  
Interactive line charts show your spending trends over time.

✅ *Bootstrap 5 Interface*  
Modern, mobile-friendly UI with modals for income updates and confirmation alerts.

---

## 🧠 AI Integration (Gemini API)

Gemini AI is used to predict categories for uncategorized expenses.
```python
if not expense.category or expense.category == 'Other':
    expense.category = gemini_predict_category(expense.name)
