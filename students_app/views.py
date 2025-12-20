from django.http import JsonResponse
from rest_framework import generics

from students_app.models import Student
from students_app.serializers import StudentReadSerializer, StudentWriteSerializer

# Create your views here.

def home(request):
    return JsonResponse({
    'title': 'Student Attitude & Behaviour API',
    'api_version': '1.0',
    'documentation_url': '<PENDING>',
    'links': {
        'self': {
            'href': '/',
            'methods': ['GET'],
            'rel': 'self',
        },
        'health': {
            'href': '/health',
            'methods': ['GET'],
            'rel': 'status',
        },
    },
})

def health(request):
    return JsonResponse({
        'service': 'Student Attitude & Behaviour API',
        'api_version': '1.0',
        'status': 'ok',
    })

class StudentListCreateView(generics.ListCreateAPIView):
    queryset = Student.objects.select_related('department', 'hobby').select_related('metrics').all()

    def get_serializer_class(self): # type: ignore[override]
        if self.request.method == 'POST':
            return StudentWriteSerializer

        return StudentReadSerializer

class StudentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Student.objects.select_related('department', 'hobby').select_related('metrics').all()

    def get_serializer_class(self): # type: ignore[override]
        if self.request.method in ('PUT', 'PATCH'):
            return StudentWriteSerializer

        return StudentReadSerializer