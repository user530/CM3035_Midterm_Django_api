from django.conf import settings
from django.db.models import ProtectedError
from django import get_version as get_django_version
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from platform import python_version as get_python_version
from pathlib import Path

from students_app.models import Student, Department, Hobby
from students_app.serializers import StudentReadSerializer, StudentWriteSerializer, DepartmentSerializer, HobbySerializer

# Helper functions
def _read_requirements() -> list[str]:
    '''
    Reads requirements.txt from BASE_DIR. Used to show in home page.
    '''
    try:
        req_path = Path(settings.BASE_DIR) / 'requirements.txt'

        if req_path.exists():
            return [
                line.strip()
                for line in req_path.read_text(encoding='utf-8').splitlines()
                if line.strip() and not line.strip().startswith('#')
            ]
    except Exception:
        pass

    return []

def _admin_block(base: str) -> dict:
    '''
    Show admin credentials only when SHOW_ADMIN_CREDS is enabled (for local debug)
    '''
    block = {'url': f'{base}/admin/'}

    show = getattr(settings, 'SHOW_ADMIN_CREDS', False)

    if show:
        block.update(
            {
                'username': getattr(settings, 'ADMIN_USERNAME', 'NOT_SET'),
                'password': getattr(settings, 'ADMIN_PASSWORD', 'NOT_SET'),
            }
        )
    return block


# === UTILITY ENDPOINTS ===
@api_view(['GET'])
def home(request):
    '''
    API home page with discovery links
    '''
    base = request.build_absolute_uri('/')[:-1]

    endpoints = {
        # Utility
        'health': f'{base}/api/health/',

        # CRUD endpoints
        'students': f'{base}/api/students',
        'student_detail': f'{base}/api/students/<pk>',
        'departments': f'{base}/api/departments',
        'department_detail': f'{base}/api/departments/<pk>',
        'hobbies': f'{base}/api/hobbies',
        'hobby_detail': f'{base}/api/hobbies/<pk>',

        # Analytics endpoints
        'students_search': f'{base}/api/students/search',
        'departments_summary': f'{base}/api/analytics/departments/summary',
        'parttime_impact': f'{base}/api/analytics/parttime/impact',
        'studytime_performance': f'{base}/api/analytics/studytime/performance',
        'risk_list': f'{base}/api/analytics/risk',
        'bmi_distribution': f'{base}/api/analytics/bmi/distribution',
    }

    return Response(
        {
            'title': 'Student Attitude & Behaviour API',
            'api_version': '1.0',
            'python_version': get_python_version(),
            'django_version': get_django_version(),

            # Extra info
            'debug': settings.DEBUG,
            'pagination': {
                'default_pagination_class': getattr(
                    settings, 'REST_FRAMEWORK', {}
                ).get('DEFAULT_PAGINATION_CLASS'),
                'page_size': getattr(settings, 'REST_FRAMEWORK', {}).get('PAGE_SIZE'),
            },

            # Admin access required
            'admin': _admin_block(base),

            # Show installed packages used (from requirements.txt)
            'packages': _read_requirements(),

            # Hyperlinks to endpoints
            'endpoints': endpoints,

            # Example URLs (show some potential options for main routes)
            'examples': {
                'list_students_page_1': f'{endpoints['students']}?page=1',
                'search_students': f'{endpoints['students_search']}?department=1&gender=Male&min_college_mark=70&limit=10',
                'department_summary': endpoints['departments_summary'],
                'risk_list': f'{endpoints['risk_list']}?stress_level=Bad&max_college_mark=60&limit=20',
                'bmi_by_gender': f'{endpoints['bmi_distribution']}?by=gender',
            },
        }
    )


@api_view(['GET'])
def health(request):
    return Response(
        {
            'service': 'Student Attitude & Behaviour API',
            'api_version': '1.0',
            'status': 'ok',
        }
    )



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