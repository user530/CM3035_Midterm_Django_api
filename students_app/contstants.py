from django.db import models

# Small helper to fix inconsistent naming in CSV data (trim+)
def normalize_str(string: str) -> str:
    return str(string).strip().casefold()

# Define enumerated field options (db value/label)

# === GENDER (I expanded existing values, just in case) ===
class Gender(models.TextChoices):
    MALE = 'Male', 'Male'
    FEMALE = 'Female', 'Female'
    OTHER = 'Other', 'Other'

# Simple str -> enum map, to use in loader script
GENDER_MAP = {
    normalize_str('Male'): Gender.MALE,
    normalize_str('Female'): Gender.FEMALE,
    normalize_str('Other'): Gender.OTHER,
}

# === DAILY STUDY ===
class DailyStudyTime(models.TextChoices):
    M0_30 = '0-30m', '0 - 30 minutes'
    M30_60 = '30-60m', '30 - 60 minutes'
    H1_2 = '1-2h', '1 - 2 hours'
    H2_3 = '2-3h', '2 - 3 hours'
    H3_4 = '3-4h', '3 - 4 hours'
    GT4H = '>4h', 'More than 4 hours'

# Map each input to both enum and numeric value (for ease of filtering/sorting)
DAILY_STUDY_TIME_MAP = {
    normalize_str('0 - 30 minute'): (DailyStudyTime.M0_30, 15),
    normalize_str('30 - 60 minute'): (DailyStudyTime.M30_60, 45),
    normalize_str('1 - 2 Hour'): (DailyStudyTime.H1_2, 90),
    normalize_str('2 - 3 hour'): (DailyStudyTime.H2_3, 150),
    normalize_str('3 - 4 hour'): (DailyStudyTime.H3_4, 210),
    normalize_str('More Than 4 hour'): (DailyStudyTime.GT4H, 270),
}

# === STUDY PREFERENCES ===
class StudyPreference(models.TextChoices):
    MORNING = 'Morning', 'Morning'
    NIGHT = 'Night', 'Night'
    ANYTIME = 'Anytime', 'Anytime'

STUDY_PREFERENCE_MAP = {
    normalize_str('Morning'): StudyPreference.MORNING,
    normalize_str('Night'): StudyPreference.NIGHT,
    normalize_str('Anytime'): StudyPreference.ANYTIME,
}

# === SOCIAL MEDIA AND VIDEO ===
class MediaVideoTime(models.TextChoices):
    M0 = '0m', '0 minutes'
    M1_30 = '1-30m', '1 - 30 minutes'
    M30_60 = '30-60m', '30 - 60 minutes'
    M60_90 = '60-90m', '1 - 1.5 hour'
    M90_120 = '90-120m', '1.5 - 2 hour'
    GT2H = '>2h', 'More than 2 hour'

MEDIA_VIDEO_TIME_MAP = {
    normalize_str('0 Minute'): (MediaVideoTime.M0, 0),
    normalize_str('1 - 30 Minute'): (MediaVideoTime.M1_30, 15),
    normalize_str('30 - 60 Minute'): (MediaVideoTime.M30_60, 45),
    normalize_str('1 - 1.30 hour'): (MediaVideoTime.M60_90, 75),
    normalize_str('1.30 - 2 hour'): (MediaVideoTime.M90_120, 105),
    normalize_str('More than 2 hour'): (MediaVideoTime.GT2H, 150),
}

# === TRAVELING TIME === 
class TravelingTime(models.TextChoices):
    M0_30 = '0-30m', '0 - 30 minutes'
    M30_60 = '30-60m', '30 - 60 minutes'
    M60_90 = '60-90m', '1 - 1.5 hour'
    M90_120 = '90-120m', '1.5 - 2 hour'
    M120_150 = '120-150m', '2 - 2.5 hour'
    M150_180 = '150-180m', '2.5 - 3 hour'
    GT3H = '>3h', 'More than 3 hour'

TRAVELING_TIME_MAP = {
    normalize_str('0 - 30 minutes'): (TravelingTime.M0_30, 15),
    normalize_str('30 - 60 minutes'): (TravelingTime.M30_60, 45),
    normalize_str('1 - 1.30 hour'): (TravelingTime.M60_90, 75),
    normalize_str('1.30 - 2 hour'): (TravelingTime.M90_120, 105),
    normalize_str('2 - 2.30 hour'): (TravelingTime.M120_150, 135),
    normalize_str('2.30 - 3 hour'): (TravelingTime.M150_180, 165),
    normalize_str('More than 3 hour'): (TravelingTime.GT3H, 195),
}

# === STRESS LEVEL ===
class StressLevel(models.TextChoices):
    GOOD = 'Good', 'Good'
    FABULOUS = 'Fabulous', 'Fabulous'
    BAD = 'Bad', 'Bad'
    AWFUL = 'Awful', 'Awful'

STRESS_LEVEL_MAP = {
    normalize_str('Awful'): StressLevel.AWFUL,
    normalize_str('Bad'): StressLevel.BAD,
    normalize_str('Good'): StressLevel.GOOD,
    normalize_str('fabulous'): StressLevel.FABULOUS,
}

# === FINANCIAL STATUS ===
class FinancialStatus(models.TextChoices):
    AWFUL = 'Awful', 'Awful'
    BAD = 'Bad', 'Bad'
    GOOD = 'Good', 'Good'
    FABULOUS = 'Fabulous', 'Fabulous'

FINANCIAL_STATUS_MAP = {
    normalize_str('Awful'): FinancialStatus.AWFUL,
    normalize_str('Bad'): FinancialStatus.BAD,
    normalize_str('Good'): FinancialStatus.GOOD,
    normalize_str('Fabulous'): FinancialStatus.FABULOUS,
}