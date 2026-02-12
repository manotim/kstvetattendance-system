#!/usr/bin/env python
"""
Script to seed courses and classes data only
Run with: python manage.py shell < scripts/seed_courses.py
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

def seed_courses():
    print("Seeding courses and classes...")
    
    # Create courses
    courses_data = [
        {
            'code': 'CS101',
            'name': 'Introduction to Computer Science',
            'description': 'Fundamentals of computer science and programming',
            'level': 'certificate',
            'duration_months': 12,
            'department': 'Computer Science'
        },
        {
            'code': 'IT201',
            'name': 'Information Technology',
            'description': 'IT infrastructure and networking basics',
            'level': 'diploma',
            'duration_months': 24,
            'department': 'ICT'
        },
        {
            'code': 'EE301',
            'name': 'Electrical Engineering',
            'description': 'Electrical circuits and power systems',
            'level': 'craft',
            'duration_months': 18,
            'department': 'Engineering'
        },
        {
            'code': 'BC401',
            'name': 'Building Construction',
            'description': 'Construction techniques and materials',
            'level': 'artisan',
            'duration_months': 9,
            'department': 'Construction'
        },
    ]
    
    courses = []
    for data in courses_data:
        course, created = Course.objects.get_or_create(
            code=data['code'],
            defaults=data
        )
        if created:
            print(f"✅ Created course: {course.code} - {course.name}")
        courses.append(course)
    
    # Get instructors
    instructors = User.objects.filter(user_type='instructor')
    
    # Create classes
    for course in courses:
        for year in ['2023/2024', '2024/2025']:
            for semester in [1, 2]:
                class_obj, created = Class.objects.get_or_create(
                    class_code=f"{course.code}-{year.split('/')[0]}-S{semester}",
                    defaults={
                        'course': course,
                        'name': f"{course.name} - Semester {semester}",
                        'instructor': random.choice(instructors) if instructors.exists() else None,
                        'academic_year': year,
                        'semester': semester,
                        'start_date': timezone.now().date() - timedelta(days=30),
                        'end_date': timezone.now().date() + timedelta(days=180),
                        'meeting_days': 'Monday, Wednesday, Friday',
                        'meeting_time': '10:00 AM - 12:00 PM',
                        'venue': f'Room {random.randint(101, 110)}',
                        'max_students': 30,
                    }
                )
                if created:
                    print(f"✅ Created class: {class_obj.class_code}")
    
    print(f"\n📊 Total courses: {Course.objects.count()}")
    print(f"📊 Total classes: {Class.objects.count()}")
    print("Courses seeding completed!")

if __name__ == '__main__':
    seed_courses()