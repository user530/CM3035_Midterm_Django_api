from django.urls import path
from . import views, analytics_views

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

    # Analytic routes ('interesting 6 endpoints' that use advanced querries and filtering)
    path('students/search', analytics_views.students_search, name='students-search'),
    path('analytics/departments/summary', analytics_views.departments_summary, name='departments-summary'),
    path('analytics/parttime/impact', analytics_views.parttime_impact, name='parttime-impact'),
    path('analytics/studytime/performance', analytics_views.studytime_performance, name='studytime-performance'),
    path('analytics/risk', analytics_views.risk_list, name='risk-list'),
    path('analytics/bmi/distribution', analytics_views.bmi_distribution, name='bmi-distribution'),
]