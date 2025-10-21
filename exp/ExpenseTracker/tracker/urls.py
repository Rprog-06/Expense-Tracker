from django.urls import path
from . import views 
from .views import update_expense

urlpatterns = [
     path("update/<int:expense_id>/", update_expense, name="update_expense"),
    path('', views.dashboard, name='dashboard'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('add/', views.add_expense, name='add_expense'),
    path('delete/<int:id>/', views.delete_expense, name='delete_expense'),
    path('set-income/', views.set_income, name='set_income'),
]
