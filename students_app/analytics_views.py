from django.db.models import Count, Avg, Q, F, FloatField, Value
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models.functions import Cast
from rest_framework import status

from typing import Optional, Any

from students_app.models import Student, Department



# === HELPERS ===
def _parse_bool(value: Optional[str]) -> Optional[bool]:
    if value is None:
        return None

    val = value.strip().lower()

    if val in ('1', 'true', 'yes', 'y', 't'):
        return True

    if val in ('0', 'false', 'no', 'n', 'f'):
        return False

    return None

def _parse_int(value: Optional[str]) -> Optional[int]:
    if value is None or value == '':
        return None

    try:
        return int(value)
    except ValueError:
        return None

def _parse_float(value: Optional[str]) -> Optional[float]:
    if value is None or value == '':
        return None

    try:
        return float(value)
    except ValueError:
        return None

def _round(value, digits=2):
    if value is None:
        return None
    return round(float(value), digits)

def _limit(value: Optional[str], default: int = 50, max_value: int = 500) -> int:
    num = _parse_int(value)

    if num is None:
        return default

    return max(1, min(num, max_value))


def _metrics_prefix() -> str:
    '''
    Adjust this if your Student->StudentMetrics relation uses related_name='metrics'.
    '''
    return 'metrics'



# === ADV.ROUTE 1: Advanced students search route (multi-filtering) ===
@api_view(['GET'])
def students_search(request):
    '''
    GET /api/students/search?department=<id>&gender=Male&part_time_job=true&stress_level=Bad&min_college_mark=70&max_college_mark=90&limit=50

    Returns a list of students with selected fields (not full serializer output).
    This endpoint proves understanding of multi-parameter filtering + joins.
    '''
    prefix = _metrics_prefix()

    # Join related entities
    querySet = Student.objects.select_related('department', 'hobby')

    # Parse and add filters if applicable
    dept_id = _parse_int(request.query_params.get('department'))
    if dept_id is not None:
        querySet = querySet.filter(department_id=dept_id)

    hobby_id = _parse_int(request.query_params.get('hobby'))
    if hobby_id is not None:
        querySet = querySet.filter(hobby_id=hobby_id)

    gender = request.query_params.get('gender')
    if gender:
        querySet = querySet.filter(gender__iexact=gender.strip())

    part_time_job = _parse_bool(request.query_params.get('part_time_job'))
    if part_time_job is not None:
        querySet = querySet.filter(**{f'{prefix}__part_time_job': part_time_job})

    stress_level = request.query_params.get('stress_level')
    if stress_level:
        querySet = querySet.filter(**{f'{prefix}__stress_level': stress_level})

    min_mark = _parse_float(request.query_params.get('min_college_mark'))
    if min_mark is not None:
        querySet = querySet.filter(**{f'{prefix}__college_mark__gte': min_mark})

    max_mark = _parse_float(request.query_params.get('max_college_mark'))
    if max_mark is not None:
        querySet = querySet.filter(**{f'{prefix}__college_mark__lte': max_mark})

    limit = _limit(request.query_params.get('limit'), default=50, max_value=500)

    # Select suitable rows (up to the limit) for analytics/search
    rows = (
        querySet.order_by('pk')
        .values(
            'pk',
            'gender',
            'height_cm',
            'weight_kg',
            'department__name',
            'hobby__name',
            f'{prefix}__college_mark',
            f'{prefix}__stress_level',
            f'{prefix}__part_time_job',
            f'{prefix}__salary_expectation',
            f'{prefix}__daily_studying_time',
            f'{prefix}__willingness_percent',
        )[:limit]
    )

    results = []
    # Populate result
    for row in rows:
        results.append(
            {
                'id': row['pk'],
                'gender': row['gender'],
                'department': row['department__name'],
                'hobby': row['hobby__name'],
                'height_cm': row['height_cm'],
                'weight_kg': row['weight_kg'],
                'college_mark': row[f'{prefix}__college_mark'],
                'stress_level': row[f'{prefix}__stress_level'],
                'part_time_job': row[f'{prefix}__part_time_job'],
                'salary_expectation': row[f'{prefix}__salary_expectation'],
                'daily_studying_time': row[f'{prefix}__daily_studying_time'],
                'willingness_percent': row[f'{prefix}__willingness_percent'],
            }
        )

    return Response(
        {
            'filters': {
                'department': dept_id,
                'hobby': hobby_id,
                'gender': gender,
                'part_time_job': part_time_job,
                'stress_level': stress_level,
                'min_college_mark': min_mark,
                'max_college_mark': max_mark,
                'limit': limit,
            },
            'count': len(results),
            'results': results,
        }
    )



# === ADV.ROUTE 2: Department summary analytics ===
@api_view(['GET'])
def departments_summary(request):
    '''
    GET /api/analytics/departments/summary

    Per department:
    - student count
    - avg college_mark
    - avg salary_expectation
    - stress distribution counts
    '''
    prefix = _metrics_prefix()

    # Generate aggregates per department
    querySet = (
        Department.objects.all()
        .annotate(
            student_count=Count('students', distinct=True),
            avg_college_mark=Avg(f'students__{prefix}__college_mark'),
            avg_salary_expectation=Avg(f'students__{prefix}__salary_expectation'),
            stress_good=Count('students', filter=Q(**{f'students__{prefix}__stress_level': 'Good'}), distinct=True),
            stress_fair=Count('students', filter=Q(**{f'students__{prefix}__stress_level': 'Fair'}), distinct=True),
            stress_bad=Count('students', filter=Q(**{f'students__{prefix}__stress_level': 'Bad'}), distinct=True),
        )
        .order_by('name')
        .values(
            'id',
            'name',
            'student_count',
            'avg_college_mark',
            'avg_salary_expectation',
            'stress_good',
            'stress_fair',
            'stress_bad',
        )
    )

    results = [
        {
            'department_id': row['id'],
            'department_name': row['name'],
            'student_count': row['student_count'],
            'avg_college_mark': _round(row['avg_college_mark']),
            'avg_salary_expectation': _round(row['avg_salary_expectation']),
            'stress_distribution': {
                'Good': row['stress_good'],
                'Fair': row['stress_fair'],
                'Bad': row['stress_bad'],
            },
        }
        for row in querySet
    ]

    return Response({'count': len(results), 'results': results})



# === ADV.ROUTE 3: Analyze effect of the part-time job ===
@api_view(['GET'])
def parttime_impact(request):
    '''
    GET /api/analytics/parttime/impact

    Compare average performance metrics for students with- and without part-time jobs.
    '''
    prefix = _metrics_prefix()

    base = Student.objects.all()

    # Aggregation helper
    def _agg(part_time: bool) -> dict[str, Any]:
        querySet = base.filter(**{f'{prefix}__part_time_job': part_time})

        result = querySet.aggregate(
            student_count=Count('pk'),
            avg_college_mark=Avg(f'{prefix}__college_mark'),
            avg_salary_expectation=Avg(f'{prefix}__salary_expectation'),
            avg_willingness_percent=Avg(f'{prefix}__willingness_percent'),
        )

        # Roud up floats
        result['avg_college_mark'] = _round(result['avg_college_mark'])
        result['avg_salary_expectation'] = _round(result['avg_salary_expectation'])
        result['avg_willingness_percent'] = _round(result['avg_willingness_percent'])

        return result

    # Aggregate for students with- and without part-time job
    with_job = _agg(True)
    without_job = _agg(False)

    return Response(
        {
            'with_part_time_job': with_job,
            'without_part_time_job': without_job,
        }
    )



# === ADV.ROUTE 4: Analyze how study time affects performance ===
@api_view(['GET'])
def studytime_performance(request):
    '''
    GET /api/analytics/studytime/performance

    Group by daily_studying_time and return:
    - count
    - avg college_mark
    - avg willingness_percent
    '''
    prefix = _metrics_prefix()

    # Select suitable rows
    querySet = (
        Student.objects.values(f'{prefix}__daily_studying_time')
        .annotate(
            student_count=Count('pk'),
            avg_college_mark=Avg(f'{prefix}__college_mark'),
            avg_willingness_percent=Avg(f'{prefix}__willingness_percent'),
        )
        .order_by(f'{prefix}__daily_studying_time')
    )

    # Populate results
    results = []
    for row in querySet:
        results.append(
            {
                'daily_studying_time': row[f'{prefix}__daily_studying_time'],
                'student_count': row['student_count'],
                'avg_college_mark': _round(row['avg_college_mark']),
                'avg_willingness_percent': _round(row['avg_willingness_percent']),
            }
        )

    return Response({'count': len(results), 'results': results})



# === ADV.ROUTE 5: Analyze students who is int he 'risk zone' with high stress/bad marks ===
@api_view(['GET'])
def risk_list(request):
    '''
    GET /api/analytics/risk?stress_level=Bad&max_college_mark=50&limit=20

    Returns a 'risk' list of students with based on stress + low mark criteria (configurable).
    '''
    prefix = _metrics_prefix()

    stress_level = request.query_params.get('stress_level') or 'Bad'
    max_mark = _parse_float(request.query_params.get('max_college_mark'))

    # Default threshold
    if max_mark is None:
        max_mark = 60.0

    limit = _limit(request.query_params.get('limit'), default=20, max_value=200)

    # Select suitable rows
    querySet = (
        Student.objects.select_related('department', 'hobby')
        .filter(**{f'{prefix}__stress_level': stress_level})
        .filter(**{f'{prefix}__college_mark__lte': max_mark})
        .order_by(F(f'{prefix}__college_mark').asc(nulls_last=True), 'pk')
    )

    rows = querySet.values(
        'pk',
        'gender',
        'department__name',
        'hobby__name',
        f'{prefix}__college_mark',
        f'{prefix}__stress_level',
        f'{prefix}__part_time_job',
    )[:limit]

    # Populate results
    results = []
    for row in rows:
        results.append(
            {
                'id': row['pk'],
                'gender': row['gender'],
                'department': row['department__name'],
                'hobby': row['hobby__name'],
                'college_mark': row[f'{prefix}__college_mark'],
                'stress_level': row[f'{prefix}__stress_level'],
                'part_time_job': row[f'{prefix}__part_time_job'],
            }
        )

    return Response(
        {
            'criteria': {'stress_level': stress_level, 'max_college_mark': max_mark, 'limit': limit},
            'count': len(results),
            'results': results,
        }
    )



# === ADV.ROUTE 6: Analyze students BMI distribution ===
@api_view(['GET'])
def bmi_distribution(request):
    '''
    GET /api/analytics/bmi/distribution
    Optional: GET /api/analytics/bmi/distribution?by=gender OR ?by=department

    BMI = weight_kg / (height_m^2)
    BMI categories:
      - underweight < 18.5
      - normal 18.5–24.9
      - overweight 25–29.9
      - obese >= 30
    '''
    # Grouping param (optional)
    by = (request.query_params.get('by') or '').strip().lower()

    # Convert height to meters inside DB expression:
    height_m = Cast(F('height_cm'), FloatField()) / Value(100.0)
    # Calculate BMI [BMI = weight_kg / (height_m^2)]
    bmi_expr = Cast(F('weight_kg'), FloatField()) / (height_m * height_m)

    # Select suitable rows
    querySet = Student.objects.annotate(bmi=bmi_expr)

    # Invalid grouping param (only allow gender/department aggregation)
    if by not in ('', 'gender', 'department'):
        return Response(
            {'detail': 'Invalid `by`. Use `gender` or `department`.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Group up
    group_fields: list[str] = []

    if by == 'gender':
        group_fields = ['gender']

    elif by == 'department':
        group_fields = ['department__name']

    # Create a copy of grouped fields
    values_fields = group_fields[:]
    # Select suitable rows and aggregate by BMI category (with/or without grouping)
    querySet2 = (
        querySet.values(*values_fields).annotate(
            total=Count('pk'),
            underweight=Count('pk', filter=Q(bmi__lt=18.5)),
            normal=Count('pk', filter=Q(bmi__gte=18.5, bmi__lt=25.0)),
            overweight=Count('pk', filter=Q(bmi__gte=25.0, bmi__lt=30.0)),
            obese=Count('pk', filter=Q(bmi__gte=30.0)),
            avg_bmi=Avg('bmi'),
        ).order_by(*values_fields) if values_fields 

        else 
            querySet.values().annotate(
                total=Count('pk'),
                underweight=Count('pk', filter=Q(bmi__lt=18.5)),
                normal=Count('pk', filter=Q(bmi__gte=18.5, bmi__lt=25.0)),
                overweight=Count('pk', filter=Q(bmi__gte=25.0, bmi__lt=30.0)),
                obese=Count('pk', filter=Q(bmi__gte=30.0)),
                avg_bmi=Avg('bmi'),
            )
    )

    # Populate result
    results = []
    for row in querySet2:
        group: dict[str, Any] = {}
        if by == 'gender':
            group = {'gender': row.get('gender')}
        elif by == 'department':
            group = {'department': row.get('department__name')}

        results.append(
            {
                **group,
                'total': row['total'],
                'avg_bmi': _round(row['avg_bmi']),
                'buckets': {
                    'underweight': row['underweight'],
                    'normal': row['normal'],
                    'overweight': row['overweight'],
                    'obese': row['obese'],
                },
            }
        )

    return Response({'group_by': by or None, 'count': len(results), 'results': results})