from django.urls import path
from .views import income_list, income_add, income_edit,income_delete,user_login,user_logout,user_register
from . import views

urlpatterns = [
    path('', income_list, name='income_list'),
    path('add/', income_add, name='income_add'),
    path('<int:pk>/edit/', income_edit, name='income_edit'),  # ✅ Correct URL pattern
    path('<int:pk>/delete/', income_delete, name='income_delete'),
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),
    path('register/', user_register, name='register'),
    path('export/excel/', views.export_to_excel, name='export_to_excel'),  # Export to Excel
    path('export/csv/', views.export_to_csv, name='export_to_csv'),   
    path('import/', views.import_income, name='import_income'),     
    
]
