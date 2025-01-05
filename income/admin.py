from django.contrib import admin
from .models import Income

@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = ('exact_date', 'amount', 'type', 'category', 'jalali_date')
    list_filter = ('type', 'category')
    search_fields = ('category',)
