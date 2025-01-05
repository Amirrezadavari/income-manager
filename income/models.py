from django.db import models
import jdatetime

class Income(models.Model):
    TYPE_CHOICES = [
        ('Cash', 'Cash'),
        ('Non-Cash', 'Non-Cash'),
    ]

    exact_date = models.DateField()  # Jalali date stored as Gregorian
    amount = models.BigIntegerField()  # Amount in IRR
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)  # Cash or Non-Cash
    category = models.CharField(max_length=100)  # Income category (from Comment column)

    def jalali_date(self):
        """Convert Gregorian date to Jalali"""
        return jdatetime.date.fromgregorian(date=self.exact_date)

    def __str__(self):
        return f"{self.jalali_date()} - {self.amount} IRR - {self.type} - {self.category}"
