from rest_framework import serializers
from django.db import transaction

from students_app.models import Student, StudentMetrics, Department, Hobby
from students_app.contstants import (
    DAILY_STUDY_TIME_MAP,
    MEDIA_VIDEO_TIME_MAP,
    TRAVELING_TIME_MAP,
)

def minutes_from_enum(map: dict[str, tuple], enum_value: str) -> int:
    '''
    Get time in minutes from the map using enum label
    '''
    for _, (enum, mins) in map.items():
        if enum == enum_value:
            return mins

    raise serializers.ValidationError(f'Unsupported enum value: {enum_value!r}')



class _NameValidationSerializer:
    '''
    Simple mixin to validate names of Department and Hobby entities. Enforces:
    - Nmae not empty
    - Trimmed name is not empty
    - Name in min/max length range after trimming
    '''
    NAME_MIN_LEN = 2
    NAME_MAX_LEN = 100

    def validate_name(self, value: str) -> str:
        if value is None:
            raise serializers.ValidationError('Name is required.')

        trimmed = value.strip()

        if not trimmed:
            raise serializers.ValidationError('Name cannot be empty or only spaces.')

        if len(trimmed) < self.NAME_MIN_LEN:
            raise serializers.ValidationError(f'Name must be at least {self.NAME_MIN_LEN} characters.')

        if len(trimmed) > self.NAME_MAX_LEN:
            raise serializers.ValidationError(f'Name must be at most {self.NAME_MAX_LEN} characters.')

        return trimmed



class DepartmentSerializer(_NameValidationSerializer, serializers.ModelSerializer):
    name = serializers.CharField(required=True, allow_blank=False)

    class Meta:
        model = Department
        fields = ['id', 'name']



class HobbySerializer(_NameValidationSerializer, serializers.ModelSerializer):
    name = serializers.CharField(required=True, allow_blank=False)

    class Meta:
        model = Hobby
        fields = ['id', 'name']



# === STUDENT SERIALIZRS ===

class StudentMetricsReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentMetrics
        # We hide foreighn key
        exclude = ['student']



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
            'metrics',
        ]
        read_only_fields = ['id']
    
    @transaction.atomic
    def create(self, validated_data):
        # Separate metrics and student data
        metrics_data = validated_data.pop('metrics')

        # Create both entities
        student = Student.objects.create(**validated_data)
        StudentMetrics.objects.create(student=student, **metrics_data)

        return student

    @transaction.atomic
    def update(self, instance, validated_data):
        metrics_data = validated_data.pop('metrics', None)

        # Update Student fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        # Update metrics (OneToOne)
        if metrics_data is not None:
            metrics = instance.metrics

            for attr, value in metrics_data.items():
                setattr(metrics, attr, value)

            metrics.save()

        return instance



class StudentWriteSerializer(serializers.ModelSerializer):
    department = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all()
    )
    hobby = serializers.PrimaryKeyRelatedField(
        queryset=Hobby.objects.all()
    )
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

    @transaction.atomic
    def create(self, validated_data):
        metrics_data = validated_data.pop('metrics')

        # Create Student entity first, then add linked metrics
        student = Student.objects.create(**validated_data)
        StudentMetrics.objects.create(student=student, **metrics_data)

        return student

    @transaction.atomic
    def update(self, instance, validated_data):
        metrics_data = validated_data.pop('metrics', None)

        # Update non metric fields first
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        # Then add metric ones
        if metrics_data is not None:
            metrics = instance.metrics

            for attr, value in metrics_data.items():
                setattr(metrics, attr, value)

            metrics.save()

        return instance