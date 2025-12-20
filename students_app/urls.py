from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('health/', views.health, name='health'),

    path('students', views.StudentListCreateView.as_view(), name='students-list'),
    path('students/<int:pk>', views.StudentDetailView.as_view(), name='students-detail'),
]