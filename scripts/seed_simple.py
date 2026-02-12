#!/usr/bin/env python
"""
Simplified seeding script that avoids contenttypes warnings
"""

import os
import sys
import django
import random
from datetime import datetime, timedelta
from django.utils import timezone

# Suppress contenttypes warnings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tvet_attendance.settings')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
django.setup()

# Now import models
from django.contrib.auth import get_user_model
from accounts.models import User as CustomUser
from courses.models import Course, Class
from students.models import Student, Enrollment
from attendance.models import AttendanceSession, AttendanceRecord

def seed_simple():
    print("🌱 SIMPLE DATA SEEDING")
    print("=" * 50)
    
    # Clear existing test data first
    print("\nClearing existing test data...")
    User = get_user_model()
    
    # Don't delete superuser, just test users
    User.objects.filter(username__in=['instructor1', 'instructor2', 'student1', 'registrar', 'hod']).delete()
    Course.objects.filter(code__in=['CS101', 'ENG201', 'BCT301']).delete()
    
    print("\n1. Creating accounts...")
    # Create admin if not exists
    admin, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@tvet.ac.ke',
            'first_name': 'System',
            'last_name': 'Admin',
            'user_type': 'admin',
            'is_staff': True,
            'is_superuser': True,
        }
    )
    if created:
        admin.set_password('admin123')
        admin.save()
        print(f"  ✅ Created admin: {admin.username}")
    
    # Create instructor
    instructor, created = User.objects.get_or_create(
        username='instructor1',
        defaults={
            'email': 'instructor@tvet.ac.ke',
            'first_name': 'John',
            'last_name': 'Kamau',
            'user_type': 'instructor',
            'department': 'Computer Science',
        }
    )
    if created:
        instructor.set_password('instructor123')
        instructor.save()
        print(f"  ✅ Created instructor: {instructor.username}")
    
    # Create student user
    student_user, created = User.objects.get_or_create(
        username='student1',
        defaults={
            'email': 'student@tvet.ac.ke',
            'first_name': 'Brian',
            'last_name': 'Mutua',
            'user_type': 'student',
        }
    )
    if created:
        student_user.set_password('student123')
        student_user.save()
        print(f"  ✅ Created student user: {student_user.username}")
    
    print("\n2. Creating courses...")
    # Create course
    course, created = Course.objects.get_or_create(
        code='CS101',
        defaults={
            'name': 'Introduction to Computer Science',
            'description': 'Basic computer science concepts',
            'level': 'certificate',
            'duration_months': 12,
            'department': 'Computer Science',
        }
    )
    if created:
        print(f"  ✅ Created course: {course.code}")
    
    print("\n3. Creating class...")
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
        print(f"  ✅ Created class: {cls.class_code}")
    
    print("\n4. Creating student profile...")
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
        print(f"  ✅ Created student: {student.admission_number}")
    
    print("\n5. Creating enrollment...")
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
        print(f"  ✅ Enrolled student in class")
    
    print("\n6. Creating attendance data...")
    # Create attendance session
    session, created = AttendanceSession.objects.get_or_create(
        class_session=cls,
        session_date=timezone.now().date(),
        defaults={
            'instructor': instructor,
            'start_time': datetime.strptime('10:00', '%H:%M').time(),
            'end_time': datetime.strptime('12:00', '%H:%M').time(),
            'topic_covered': 'Introduction to Python',
            'venue': cls.venue,
            'attendance_method': 'manual',
            'status': 'ongoing',
        }
    )
    if created:
        print(f"  ✅ Created attendance session")
    
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
        print(f"  ✅ Created attendance record")
    
    print("\n" + "=" * 50)
    print("✅ MINIMAL DATA SEEDING COMPLETE")
    print("\n🔐 LOGIN CREDENTIALS:")
    print(f"  Admin:     username='admin', password='admin123'")
    print(f"  Instructor: username='instructor1', password='instructor123'")
    print(f"  Student:   username='student1', password='student123'")
    print(f"             Admission: TVET2024001")
    print("\n🌐 Access the system at: http://127.0.0.1:8000/")

if __name__ == '__main__':
    seed_simple()