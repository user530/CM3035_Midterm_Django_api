from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from students_app.contstants import (
    Gender, 
    DailyStudyTime, 
    MediaVideoTime, 
    TravelingTime, 
    StressLevel, 
    FinancialStatus,
    StudyPreference,
)

# Create your models here.

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)

    # Default sorting order
    class Meta:
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


class Hobby(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


class Student(models.Model):
    gender = models.CharField(
        max_length=10, 
        choices=Gender.choices, 
        db_index=True
    )

    # Prevent 'accidental' deletion if there are rows depending on that department
    department = models.ForeignKey(
        Department, 
        on_delete=models.PROTECT, 
        related_name='students', 
    )

    height_cm = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(50), MaxValueValidator(250)],
        db_index=True,
    )

    weight_kg = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(20), MaxValueValidator(300)],
        db_index=True,
    )

    hobby = models.ForeignKey(
        Hobby, 
        on_delete=models.PROTECT, 
        related_name='students'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        ordering = ['id']

    def __str__(self) -> str:
        return f'Student #{self.pk} ({self.department})'


class StudentMetrics(models.Model):
    '''
    Separated table for student survey fields + numeric helper fields (minutes, percents).
    This way we keep Student model clean and makea analytics easier.
    '''
    # We dont keep metrics w/o students, so just delete them too
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='metrics')

    certification_course = models.BooleanField(default=False)

    mark_10th = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        db_index=True,
    )

    mark_12th = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        db_index=True,
    )

    college_mark = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        db_index=True
    )

    daily_studying_time = models.CharField(
        max_length=20, 
        choices=DailyStudyTime.choices,
    )

    prefer_to_study_in = models.CharField(
        max_length=10, 
        choices=StudyPreference.choices
    )

    salary_expectation = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(10_000_000)],
        db_index=True,
    )

    likes_degree = models.BooleanField(default=False)

    willingness_percent = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        db_index=True
    )

    social_media_video = models.CharField(
        max_length=20, 
        choices=MediaVideoTime.choices,
    )

    travelling_time = models.CharField(
        max_length=20, 
        choices=TravelingTime.choices,
    )

    stress_level = models.CharField(
        max_length=20, 
        choices=StressLevel.choices, 
        db_index=True
    )

    financial_status = models.CharField(
        max_length=10,
        choices=FinancialStatus.choices,
        db_index=True,
    )

    part_time_job = models.BooleanField(default=False)

    # Integer fields to allow smoother filtering/sorting, between 0 and 1440 (24h)
    study_minutes = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(1440)],
        db_index=True
    )

    social_minutes = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(1440)],
        db_index=True
    )

    travel_minutes = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(1440)],
        db_index=True
    )

    class Meta:
        # Order using id of the student entry
        ordering = ['student__id']

    def __str__(self) -> str:
        return f'Metrics for Student #{self.student.pk}'