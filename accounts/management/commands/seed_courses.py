from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from accounts.models import User
from courses.models import Course, Class

class Command(BaseCommand):
    help = 'Seed courses and classes'

    def handle(self, *args, **kwargs):
        # Get instructor
        instructor = User.objects.filter(user_type='instructor').first()
        
        if not instructor:
            self.stdout.write(self.style.ERROR('No instructor found. Run seed_accounts first.'))
            return
        
        # Create course
        course, created = Course.objects.get_or_create(
            code='CS101',
            defaults={
                'name': 'Introduction to Computer Science',
                'description': 'Basic computer science concepts and programming fundamentals',
                'level': 'certificate',
                'duration_months': 12,
                'department': 'Computer Science',
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created course: {course.code}'))
        
        # Create class
        cls, created = Class.objects.get_or_create(
            class_code='CS101-2024-S1',
            defaults={
                'course': course,
                'name': 'CS101 Semester 1',
                'instructor': instructor,
                'academic_year': '2024/2025',
                'semester': 1,
                'start_date': timezone.now().date() - timedelta(days=30),
                'end_date': timezone.now().date() + timedelta(days=180),
                'meeting_days': 'Monday, Wednesday',
                'meeting_time': '10:00 AM - 12:00 PM',
                'venue': 'Room 101',
                'max_students': 30,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created class: {cls.class_code}'))
        
        self.stdout.write(self.style.SUCCESS('Courses seeded successfully!'))