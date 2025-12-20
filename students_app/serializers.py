from rest_framework import serializers
from django.db import transaction

from students_app.models import Student, StudentMetrics, Department, Hobby
from students_app.contstants import (
    DAILY_STUDY_TIME_MAP,
    MEDIA_VIDEO_TIME_MAP,
    TRAVELING_TIME_MAP,
)

TIME_MAP_TYPE = DAILY_STUDY_TIME_MAP | MEDIA_VIDEO_TIME_MAP | TRAVELING_TIME_MAP

def minutes_from_enum(map: dict[str, tuple], enum_value: str) -> int:
    '''
    Get time in minutes from the map using enum label
    '''
    for _, (enum, mins) in map.items():
        if enum == enum_value:
            return mins

    raise serializers.ValidationError(f'Unsupported enum value: {enum_value!r}')



class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name']



class HobbySerializer(serializers.ModelSerializer):
    class Meta:
        model = Hobby
        fields = ['id', 'name']



class StudentMetricsReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentMetrics
        # We hide foreighn key
        exclude = ['student']



class StudentReadSerializer(serializers.ModelSerializer):
    department = DepartmentSerializer(read_only=True)
    hobby = HobbySerializer(read_only=True)
    metrics = StudentMetricsReadSerializer(read_only=True)

    class Meta:
        model = Student
        fields = [
            'id',
            'gender',
            'department',
            'height_cm',
            'weight_kg',
            'hobby',
            'created_at',
            'metrics',
        ]



class StudentMetricsWriteSerializer(serializers.ModelSerializer):
    # Prevent clients from providing minutes directly, we compute that field ourselves
    study_minutes = serializers.IntegerField(read_only=True)
    social_minutes = serializers.IntegerField(read_only=True)
    travel_minutes = serializers.IntegerField(read_only=True)

    class Meta:
        model = StudentMetrics
        exclude = ['student']

    # Populate 'calc' field using enum value
    def validate(self, attrs):
        if 'daily_studying_time' in attrs:
            attrs['study_minutes'] = minutes_from_enum(DAILY_STUDY_TIME_MAP, attrs['daily_studying_time'])
        if 'social_media_video' in attrs:
            attrs['social_minutes'] = minutes_from_enum(MEDIA_VIDEO_TIME_MAP, attrs['social_media_video'])
        if 'travelling_time' in attrs:
            attrs['travel_minutes'] = minutes_from_enum(TRAVELING_TIME_MAP, attrs['travelling_time'])

        return attrs



class StudentWriteSerializer(serializers.ModelSerializer):
    department = serializers.CharField(write_only=True)
    hobby = serializers.CharField(write_only=True)
    metrics = StudentMetricsWriteSerializer()

    class Meta:
        model = Student
        fields = [
            'id',
            'gender',
            'department',
            'height_cm',
            'weight_kg',
            'hobby',
            'metrics',
        ]
        read_only_fields = ['id']

    def _get_or_create_department(self, name: str) -> Department:
        '''
        Helper to get already existing or create new Department, basedon name
        '''
        name = str(name).strip()

        if not name:
            raise serializers.ValidationError({'department': 'Department name is required!'})

        dept, _ = Department.objects.get_or_create(name=name)

        return dept

    def _get_or_create_hobby(self, name: str) -> Hobby:
        '''
        Same for hobby
        '''
        name = str(name).strip()

        if not name:
            raise serializers.ValidationError({'hobby': 'Hobby name is required!'})

        hobby, _ = Hobby.objects.get_or_create(name=name)

        return hobby

    @transaction.atomic
    def create(self, validated_data):
        dept_name = validated_data.pop('department')
        hobby_name = validated_data.pop('hobby')
        metrics_data = validated_data.pop('metrics')

        dept = self._get_or_create_department(dept_name)
        hobby = self._get_or_create_hobby(hobby_name)

        # Create student entity
        student = Student.objects.create(
            department=dept,
            hobby=hobby,
            **validated_data
        )

        # Create linked studenr metrics 
        StudentMetrics.objects.create(student=student, **metrics_data)

        return student

    @transaction.atomic
    def update(self, instance, validated_data):
        # Update related fields
        if 'department' in validated_data:
            instance.department = self._get_or_create_department(validated_data.pop('department'))

        if 'hobby' in validated_data:
            instance.hobby = self._get_or_create_hobby(validated_data.pop('hobby'))

        metrics_data = validated_data.pop('metrics', None)

        # Update oher student fields (other non department/hobby)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Update student entity
        instance.save()

        # Iterate over student metrics
        if metrics_data is not None:
            metrics = instance.metrics
            # Update student metrics
            for attr, value in metrics_data.items():
                setattr(metrics, attr, value)

            metrics.save()

        return instance