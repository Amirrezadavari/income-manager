from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, authenticate, login
from django.shortcuts import render, redirect, get_object_or_404
from django.forms import ModelForm
from django.core.paginator import Paginator
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Q, Sum, Count,Avg
from django.db.models.functions import TruncMonth
from django.utils.dateparse import parse_date
from django.contrib.auth.models import User
from django import forms
from django_filters import FilterSet, DateFilter, ChoiceFilter,NumberFilter
import pandas as pd
import json
from khayyam import JalaliDate
from .models import Income
from .utils import import_excel
from datetime import datetime

class IncomeFilter(FilterSet):
    start_date = DateFilter(field_name='exact_date', lookup_expr='gte')
    end_date = DateFilter(field_name='exact_date', lookup_expr='lte')
    amount__gt = NumberFilter(field_name='amount', lookup_expr='gt')
    amount__lt = NumberFilter(field_name='amount', lookup_expr='lt')
    
    category = ChoiceFilter(
        field_name='category',
        choices=[(c, c) for c in Income.objects.values_list('category', flat=True).distinct().order_by('category')],
        empty_label="All Categories"
    )
    
    class Meta:
        model = Income
        fields = {
            'amount': ['gt', 'lt'],
            'type': ['exact'],
        }


class IncomeForm(ModelForm):
    class Meta:
        model = Income
        fields = ['exact_date', 'amount', 'type', 'category']
        widgets = {
            'exact_date': forms.DateInput(attrs={'type': 'date'}),
            'amount': forms.NumberInput(attrs={'min': '0'}),
        }

@login_required
def income_list(request):
    """Display filtered income records with pagination and statistics."""
    incomes = Income.objects.all().order_by('-exact_date')

    # Apply filters
    income_filter = IncomeFilter(request.GET, queryset=incomes)
    filtered_incomes = income_filter.qs

    # Get start and end dates from request
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Statistics for charts
    monthly_stats = (
        filtered_incomes
        .annotate(month=TruncMonth('exact_date'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )

    # Enhanced Pie Chart Data for Cash vs Non-Cash
    type_stats = (
        filtered_incomes
        .values('type')
        .annotate(
            total=Sum('amount'),
            count=Count('id')
        )
        .order_by('type')
    )

    # Calculate totals
    total_amount = filtered_incomes.aggregate(Sum('amount'))['amount__sum'] or 0
    total_records = filtered_incomes.count()

    # Calculate number of months for average
    if start_date and end_date:
        # Both dates provided
        start_jalali = JalaliDate(datetime.strptime(start_date, '%Y-%m-%d').date())
        end_jalali = JalaliDate(datetime.strptime(end_date, '%Y-%m-%d').date())
        num_months = ((end_jalali.year - start_jalali.year) * 12 + 
                     end_jalali.month - start_jalali.month + 1)
    
    elif start_date:
        # Only start date provided
        start_jalali = JalaliDate(datetime.strptime(start_date, '%Y-%m-%d').date())
        current_jalali = JalaliDate.today()
        num_months = ((current_jalali.year - start_jalali.year) * 12 + 
                     current_jalali.month - start_jalali.month + 1)
    
    elif end_date:
        # Only end date provided
        end_jalali = JalaliDate(datetime.strptime(end_date, '%Y-%m-%d').date())
        first_record = filtered_incomes.order_by('exact_date').first()
        if first_record:
            first_jalali = JalaliDate(first_record.exact_date)
            num_months = ((end_jalali.year - first_jalali.year) * 12 + 
                         end_jalali.month - first_jalali.month + 1)
        else:
            num_months = 1
    
    else:
        # No dates provided - calculate months between first and last record
        first_record = filtered_incomes.order_by('exact_date').first()
        last_record = filtered_incomes.order_by('-exact_date').first()
        
        if first_record and last_record:
            first_jalali = JalaliDate(first_record.exact_date)
            last_jalali = JalaliDate(last_record.exact_date)
            num_months = ((last_jalali.year - first_jalali.year) * 12 + 
                        last_jalali.month - first_jalali.month + 1)
        else:
            num_months = 1


    # Calculate average
    average_amount = total_amount // num_months if num_months > 0 else 0

    # Pagination
    paginator = Paginator(filtered_incomes, 50)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    # Convert dates to Jalali for display
    for income in page_obj:
        income.jalali_date = JalaliDate(income.exact_date).strftime('%Y-%m-%d')

    # Prepare chart data
    chart_data = {
        'monthly': {
            'labels': [item['month'].strftime('%Y-%m') for item in monthly_stats],
            'data': [float(item['total']) for item in monthly_stats]
        },
        'type': {
            'labels': [f"{item['type']}" for item in type_stats],
            'data': [float(item['total']) for item in type_stats],
            'percentages': [
                round((float(item['total']) / total_amount * 100 if total_amount else 0), 1)
                for item in type_stats
            ]
        }
    }

    context = {
        'page_obj': page_obj,
        'filter': income_filter,
        'chart_data': json.dumps(chart_data),
        'total_amount': total_amount,
        'total_records': total_records,
        'average_amount': int(average_amount),
    }

    return render(request, 'income_list.html', context)


@login_required
def income_add(request):
    if request.method == "POST":
        form = IncomeForm(request.POST)
        if form.is_valid():
            income = form.save(commit=False)
            income.save()
            messages.success(request, "Income record added successfully.")
            return redirect('income_list')
    else:
        form = IncomeForm()
    return render(request, 'income_form.html', {'form': form})

@login_required
def income_edit(request, pk):
    income = get_object_or_404(Income, pk=pk)
    if request.method == "POST":
        form = IncomeForm(request.POST, instance=income)
        if form.is_valid():
            form.save()
            messages.success(request, "Income record updated successfully.")
            return redirect('income_list')
    else:
        form = IncomeForm(instance=income)
    return render(request, 'income_form.html', {'form': form, 'edit': True})

@login_required
def income_delete(request, pk):
    income = get_object_or_404(Income, pk=pk)
    if request.method == "POST":
        income.delete()
        messages.success(request, "Income record deleted successfully.")
        return redirect('income_list')
    return render(request, 'income_confirm_delete.html', {'income': income})

class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("password") != cleaned_data.get("confirm_password"):
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data

def user_register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.save()
            login(request, user)
            messages.success(request, "Registration successful!")
            return redirect('income_list')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})

def user_login(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {username}!")
            return redirect('income_list')
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'login.html')

def user_logout(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')

@login_required
def export_to_excel(request):
    incomes = Income.objects.all().values('exact_date', 'amount', 'type', 'category')
    df = pd.DataFrame(list(incomes))
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="income_records.xlsx"'
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Income Records')
    return response

@login_required
def export_to_csv(request):
    incomes = Income.objects.all().values('exact_date', 'amount', 'type', 'category')
    df = pd.DataFrame(list(incomes))
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="income_records.csv"'
    df.to_csv(response, index=False)
    return response

@login_required
def import_income(request):
    if request.method == 'POST':
        uploaded_file = request.FILES.get('file')
        if uploaded_file:
            try:
                success, error = import_excel(uploaded_file)
                if success:
                    messages.success(request, "Income data imported successfully.")
                else:
                    messages.error(request, f"Error importing data: {error}")
            except Exception as e:
                messages.error(request, f"Error processing file: {str(e)}")
        else:
            messages.error(request, "No file was uploaded.")
        return redirect('income_list')
    return render(request, 'import_income.html')
