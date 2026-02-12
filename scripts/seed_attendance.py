#!/usr/bin/env python
"""
Script to seed attendance data only
Run with: python manage.py shell < scripts/seed_attendance.py
"""

import os
import sys
import django
import random
from datetime import datetime, timedelta
from django.utils import timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tvet_attendance.settings')
django.setup()

from accounts.models import User
from courses.models import Class
from students.models import Enrollment
from attendance.models import AttendanceSession, AttendanceRecord, ExcuseApplication

def seed_attendance():
    print("Seeding attendance data...")
    
    # Check prerequisites
    classes = Class.objects.filter(is_active=True)
    if not classes.exists():
        print("❌ No classes found. Please seed courses and classes first.")
        return
    
    # Create attendance sessions for the past 7 days
    today = timezone.now().date()
    attendance_sessions = []
    
    for i in range(7):
        session_date = today - timedelta(days=i)
        
        # Skip weekends
        if session_date.weekday() >= 5:
            continue
        
        for class_obj in random.sample(list(classes), min(3, len(classes))):
            # Create attendance session
            session = AttendanceSession.objects.create(
                class_session=class_obj,
                instructor=class_obj.instructor,
                session_date=session_date,
                start_time=datetime.strptime('10:00', '%H:%M').time(),
                end_time=datetime.strptime('12:00', '%H:%M').time(),
                topic_covered=f"Session {i+1} - {class_obj.course.name}",
                venue=class_obj.venue,
                attendance_method='manual',
                status='completed',
            )
            attendance_sessions.append(session)
            
            # Get enrolled students
            enrollments = Enrollment.objects.filter(class_enrolled=class_obj, is_active=True)
            
            # Create attendance records
            for enrollment in enrollments:
                # Random attendance status
                status = random.choices(
                    ['present', 'absent', 'late'],
                    weights=[0.7, 0.2, 0.1],
                    k=1
                )[0]
                
                check_in_time = None
                if status in ['present', 'late']:
                    check_in_time = timezone.make_aware(datetime.combine(
                        session_date,
                        session.start_time
                    )) + timedelta(minutes=random.randint(-5, 30))
                
                AttendanceRecord.objects.create(
                    session=session,
                    student=enrollment.student,
                    status=status,
                    check_in_time=check_in_time,
                    marked_by=class_obj.instructor,
                )
            
            # Update session statistics
            session.calculate_stats()
            
            print(f"✅ Created attendance session: {class_obj.class_code} on {session_date}")
    
    # Create some excuse applications
    print("\nCreating excuse applications...")
    students = Enrollment.objects.values_list('student', flat=True).distinct()[:5]
    
    for student_id in students:
        from students.models import Student
        student = Student.objects.get(id=student_id)
        
        # Get a class the student is enrolled in
        enrollment = Enrollment.objects.filter(student=student, is_active=True).first()
        if enrollment:
            ExcuseApplication.objects.create(
                student=student,
                class_session=enrollment.class_enrolled,
                reason='Medical appointment',
                start_date=today - timedelta(days=2),
                end_date=today,
                status='approved',
                reviewed_by=User.objects.filter(user_type='instructor').first(),
                review_notes='Approved with documentation',
                reviewed_at=timezone.now(),
            )
            print(f"✅ Created excuse application for {student.admission_number}")
    
    print(f"\n📊 Total attendance sessions: {AttendanceSession.objects.count()}")
    print(f"📊 Total attendance records: {AttendanceRecord.objects.count()}")
    print(f"📊 Total excuse applications: {ExcuseApplication.objects.count()}")
    print("Attendance seeding completed!")

if __name__ == '__main__':
    seed_attendance()