from django.db import models
from django.db import models
from django.contrib.auth.models import User

class Expense(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
 
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(auto_now_add=False, auto_now=False)
    CATEGORY_CHOICES = [
    ('Food', 'Food'),
    ('Travel', 'Travel'),
    ('Entertainment', 'Entertainment'),
    ('Health', 'Health'),
    ('Bills', 'Bills'),
    ('Shopping', 'Shopping'),
    ('Other', 'Other'),
]

    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES, default='Other')


    def __str__(self):
        return self.name
class Income(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.user.username}'s Income: {self.amount}"

# Create your models here.
