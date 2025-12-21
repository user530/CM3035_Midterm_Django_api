from django.http import JsonResponse
from django.db.models import ProtectedError
from rest_framework import generics, status
from rest_framework.response import Response

from students_app.models import Student, Department, Hobby
from students_app.serializers import StudentReadSerializer, StudentWriteSerializer, DepartmentSerializer, HobbySerializer

# Create your views here.

def home(request):
    return JsonResponse({
    'title': 'Student Attitude & Behaviour API',
    'api_version': '1.0',
    'documentation_url': '<PENDING>',
    'links': {
        'self': {'href': '/', 'methods': ['GET'], 'rel': 'self'},
        'health': {'href': '/health', 'methods': ['GET'], 'rel': 'status'},
        'students': {'href': '/students', 'methods': ['GET', 'POST'], 'rel': 'collection'},
        'departments': {'href': '/departments', 'methods': ['GET', 'POST'], 'rel': 'collection'},
        'hobbies': {'href': '/hobbies', 'methods': ['GET', 'POST'], 'rel': 'collection'},
    },
})

def health(request):
    return JsonResponse({
        'service': 'Student Attitude & Behaviour API',
        'api_version': '1.0',
        'status': 'ok',
    })



# === STUDENTS CRUD ===

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



# === DEPARTMENT CRUD ===

class DepartmentListCreateView(generics.ListCreateAPIView):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer


class DepartmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer

    # Return error response on attempt to delete protected department (referenced by some mertic)
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        try:
            self.perform_destroy(instance)
        except ProtectedError:
            return Response(
                {'detail': 'Cannot delete: this department is still referenced by one or more students.'},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)



# === HOBBIES CRUD ===

class HobbyListCreateView(generics.ListCreateAPIView):
    queryset = Hobby.objects.all()
    serializer_class = HobbySerializer


class HobbyDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Hobby.objects.all()
    serializer_class = HobbySerializer

    # Return error response on attempt to delete protected hobby (referenced by some mertic)
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            self.perform_destroy(instance)
        except ProtectedError:
            return Response(
                {'detail': 'Cannot delete: this hobby is still referenced by one or more students.'},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)