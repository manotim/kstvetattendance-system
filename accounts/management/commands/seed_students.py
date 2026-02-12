from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from accounts.models import User
from courses.models import Course, Class
from students.models import Student, Enrollment

class Command(BaseCommand):
    help = 'Seed students data'

    def handle(self, *args, **kwargs):
        # Get course and class
        course = Course.objects.filter(code='CS101').first()
        cls = Class.objects.filter(class_code='CS101-2024-S1').first()
        
        if not course or not cls:
            self.stdout.write(self.style.ERROR('Course or class not found. Run seed_courses first.'))
            return
        
        # Get student user
        student_user = User.objects.filter(username='student1').first()
        
        if not student_user:
            self.stdout.write(self.style.ERROR('Student user not found. Run seed_accounts first.'))
            return
        
        # Create student profile
        student, created = Student.objects.get_or_create(
            user=student_user,
            defaults={
                'admission_number': 'TVET2024001',
                'date_of_birth': timezone.now().date() - timedelta(days=20*365),
                'gender': 'M',
                'address': 'P.O. Box 123, Kitui',
                'county': 'Kitui',
                'sub_county': 'Central',
                'national_id': '12345678',
                'emergency_contact_name': 'John Mutua',
                'emergency_contact_phone': '0712345678',
                'emergency_contact_relationship': 'Father',
                'course': course,
                'year_of_admission': 2024,
                'status': 'active',
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created student: {student.admission_number}'))
        
        # Create enrollment
        enrollment, created = Enrollment.objects.get_or_create(
            student=student,
            class_enrolled=cls,
            defaults={
                'course': course,
                'enrollment_type': 'regular',
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Enrolled student in class'))
        
        self.stdout.write(self.style.SUCCESS('Students seeded successfully!'))