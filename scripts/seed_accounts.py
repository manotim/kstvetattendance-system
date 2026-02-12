#!/usr/bin/env python
"""
Script to seed accounts data only
Run with: python manage.py shell < scripts/seed_accounts.py
"""

import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tvet_attendance.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def seed_accounts():
    print("Seeding accounts data...")
    
    # Super Admin
    admin, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@tvet.ac.ke',
            'first_name': 'System',
            'last_name': 'Administrator',
            'user_type': 'admin',
            'is_staff': True,
            'is_superuser': True,
        }
    )
    if created:
        admin.set_password('admin123')
        admin.save()
        print(f"✅ Created admin: {admin.username}")
    
    # Instructors
    instructors = [
        {'username': 'john_doe', 'first_name': 'John', 'last_name': 'Doe', 'email': 'john.doe@tvet.ac.ke'},
        {'username': 'jane_smith', 'first_name': 'Jane', 'last_name': 'Smith', 'email': 'jane.smith@tvet.ac.ke'},
        {'username': 'robert_kim', 'first_name': 'Robert', 'last_name': 'Kim', 'email': 'robert.kim@tvet.ac.ke'},
        {'username': 'sarah_lee', 'first_name': 'Sarah', 'last_name': 'Lee', 'email': 'sarah.lee@tvet.ac.ke'},
    ]
    
    for instructor_data in instructors:
        instructor, created = User.objects.get_or_create(
            username=instructor_data['username'],
            defaults={
                'email': instructor_data['email'],
                'first_name': instructor_data['first_name'],
                'last_name': instructor_data['last_name'],
                'user_type': 'instructor',
                'department': 'Academic',
            }
        )
        if created:
            instructor.set_password('instructor123')
            instructor.save()
            print(f"✅ Created instructor: {instructor_data['first_name']} {instructor_data['last_name']}")
    
    # Registrar
    registrar, created = User.objects.get_or_create(
        username='registrar',
        defaults={
            'email': 'registrar@tvet.ac.ke',
            'first_name': 'Samuel',
            'last_name': 'Johnson',
            'user_type': 'registrar',
        }
    )
    if created:
        registrar.set_password('registrar123')
        registrar.save()
        print(f"✅ Created registrar: {registrar.username}")
    
    # HOD
    hod, created = User.objects.get_or_create(
        username='hod',
        defaults={
            'email': 'hod@tvet.ac.ke',
            'first_name': 'Dr. James',
            'last_name': 'Wilson',
            'user_type': 'hod',
            'department': 'Computer Science',
        }
    )
    if created:
        hod.set_password('hod123')
        hod.save()
        print(f"✅ Created HOD: {hod.username}")
    
    # Sample Students
    for i in range(10):
        student, created = User.objects.get_or_create(
            username=f'student{i+1}',
            defaults={
                'email': f'student{i+1}@tvet.ac.ke',
                'first_name': f'Student{i+1}',
                'last_name': f'Demo{i+1}',
                'user_type': 'student',
            }
        )
        if created:
            student.set_password('student123')
            student.save()
            print(f"✅ Created student: student{i+1}")
    
    print(f"\n📊 Total users: {User.objects.count()}")
    print("Accounts seeding completed!")

if __name__ == '__main__':
    seed_accounts()