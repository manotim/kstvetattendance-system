#!/usr/bin/env python
"""
Script to seed students data only
Run with: python manage.py shell < scripts/seed_students.py
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
from courses.models import Course, Class
from students.models import Student, Enrollment, AcademicRecord

def seed_students():
    print("Seeding students data...")
    
    # Get courses
    courses = Course.objects.all()
    if not courses.exists():
        print("❌ No courses found. Please seed courses first.")
        return
    
    # Create 20 sample students
    for i in range(20):
        username = f'student_demo_{i+1}'
        
        if User.objects.filter(username=username).exists():
            continue
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=f'student{i+1}@tvet.ac.ke',
            first_name=f'Student{i+1}',
            last_name='Demo',
            user_type='student',
            password='student123',
        )
        
        # Create student profile
        student = Student.objects.create(
            user=user,
            date_of_birth=timezone.now().date() - timedelta(days=random.randint(18*365, 22*365)),
            gender=random.choice(['M', 'F']),
            address=f'P.O. Box {1000 + i}',
            county='Kitui',
            sub_county=random.choice(['Central', 'West', 'East']),
            national_id=f'{20000000 + i}',
            emergency_contact_name=f'Guardian {i+1}',
            emergency_contact_phone=f'0712{random.randint(100000, 999999)}',
            emergency_contact_relationship='Parent',
            course=random.choice(courses),
            year_of_admission=2024,
            status='active',
        )
        
        print(f"✅ Created student: {student.admission_number} - {user.get_full_name()}")
    
    # Create enrollments
    students = Student.objects.all()
    classes = Class.objects.filter(is_active=True)
    
    print("\nCreating enrollments...")
    for student in students:
        # Enroll in 1-2 classes from student's course
        student_classes = classes.filter(course=student.course)[:random.randint(1, 2)]
        
        for class_obj in student_classes:
            Enrollment.objects.get_or_create(
                student=student,
                class_enrolled=class_obj,
                defaults={
                    'course': student.course,
                    'enrollment_type': 'regular',
                }
            )
            print(f"   Enrolled {student.admission_number} in {class_obj.class_code}")
    
    # Create academic records
    print("\nCreating academic records...")
    for student in random.sample(list(students), 10):  # 10 random students
        for semester in [1, 2]:
            AcademicRecord.objects.create(
                student=student,
                module_code=f"{student.course.code[:3]}101",
                module_name=f"Introduction to {student.course.name.split()[0]}",
                grade=random.choice(['A', 'B', 'C']),
                score=random.uniform(70, 90),
                semester=semester,
                academic_year='2023/2024',
            )
    
    print(f"\n📊 Total students: {Student.objects.count()}")
    print(f"📊 Total enrollments: {Enrollment.objects.count()}")
    print(f"📊 Total academic records: {AcademicRecord.objects.count()}")
    print("Students seeding completed!")

if __name__ == '__main__':
    seed_students()