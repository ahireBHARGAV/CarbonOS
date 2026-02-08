from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import path
from carbon_app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.employee_wizard_view, name='wizard'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
    path('my-dashboard/', views.employee_dashboard_select_view, name='employee_dashboard_select'),
    path('my-dashboard/<int:employee_id>/', views.employee_dashboard_view, name='employee_dashboard'),
]
