from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('health/', views.health, name='health'),

    # Student routes
    path('students', views.StudentListCreateView.as_view(), name='students-list'),
    path('students/<int:pk>', views.StudentDetailView.as_view(), name='students-detail'),

    # Department routes
    path('departments', views.DepartmentListCreateView.as_view(), name='departments-list'),
    path('departments/<int:pk>', views.DepartmentDetailView.as_view(), name='departments-detail'),

    # Hobby routes
    path('hobbies', views.HobbyListCreateView.as_view(), name='hobbies-list'),
    path('hobbies/<int:pk>', views.HobbyDetailView.as_view(), name='hobbies-detail'),
]