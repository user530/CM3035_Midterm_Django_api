from django.contrib import admin
from .models import Student, Department, Hobby, StudentMetrics

# Register your models here.
admin.site.register(Student)
admin.site.register(StudentMetrics)
admin.site.register(Department)
admin.site.register(Hobby)
