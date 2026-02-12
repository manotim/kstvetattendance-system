from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from accounts.models import User
from courses.models import Class
from students.models import Student, Enrollment
from attendance.models import AttendanceSession, AttendanceRecord

class Command(BaseCommand):
    help = 'Seed attendance data'

    def handle(self, *args, **kwargs):
        # Get class, instructor, and student
        cls = Class.objects.filter(class_code='CS101-2024-S1').first()
        instructor = User.objects.filter(username='instructor1').first()
        student = Student.objects.filter(admission_number='TVET2024001').first()
        
        if not cls or not instructor or not student:
            self.stdout.write(self.style.ERROR('Required data not found. Run previous seeders first.'))
            return
        
        # Create attendance session for today
        session, created = AttendanceSession.objects.get_or_create(
            class_session=cls,
            session_date=timezone.now().date(),
            defaults={
                'instructor': instructor,
                'start_time': datetime.strptime('10:00', '%H:%M').time(),
                'end_time': datetime.strptime('12:00', '%H:%M').time(),
                'topic_covered': 'Introduction to Python Programming',
                'venue': cls.venue,
                'attendance_method': 'manual',
                'status': 'ongoing',
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created attendance session'))
        
        # Create attendance record
        record, created = AttendanceRecord.objects.get_or_create(
            session=session,
            student=student,
            defaults={
                'status': 'present',
                'check_in_time': timezone.now() - timedelta(minutes=30),
                'marked_by': instructor,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created attendance record'))
        
        # Update session statistics
        session.calculate_stats()
        
        self.stdout.write(self.style.SUCCESS('Attendance seeded successfully!'))