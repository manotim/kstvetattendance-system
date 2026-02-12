#!/usr/bin/env python
"""
Verify that data was seeded correctly
"""

import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tvet_attendance.settings')
django.setup()

from django.contrib.auth import get_user_model
from courses.models import Course, Class
from students.models import Student, Enrollment, AcademicRecord
from attendance.models import AttendanceSession, AttendanceRecord, ExcuseApplication
from reports.models import ReportTemplate, DashboardWidget, GeneratedReport

User = get_user_model()

def verify_data():
    print("🔍 VERIFYING SEEDED DATA")
    print("=" * 50)
    
    # Check accounts
    print("\n📋 ACCOUNTS:")
    print(f"  Total Users: {User.objects.count()}")
    print(f"  Admins: {User.objects.filter(user_type='admin').count()}")
    print(f"  Instructors: {User.objects.filter(user_type='instructor').count()}")
    print(f"  Students: {User.objects.filter(user_type='student').count()}")
    print(f"  Registrars: {User.objects.filter(user_type='registrar').count()}")
    print(f"  HODs: {User.objects.filter(user_type='hod').count()}")
    
    # Check courses
    print("\n📚 COURSES:")
    print(f"  Total Courses: {Course.objects.count()}")
    courses = Course.objects.all()
    for course in courses[:3]:  # Show first 3
        print(f"  - {course.code}: {course.name}")
    
    # Check classes
    print("\n🏫 CLASSES:")
    print(f"  Total Classes: {Class.objects.count()}")
    classes = Class.objects.all()[:3]
    for cls in classes:
        print(f"  - {cls.class_code}: {cls.course.code}")
    
    # Check students
    print("\n👨‍🎓 STUDENTS:")
    print(f"  Total Students: {Student.objects.count()}")
    students = Student.objects.all()[:3]
    for student in students:
        print(f"  - {student.admission_number}: {student.user.get_full_name()}")
    
    # Check enrollments
    print("\n📝 ENROLLMENTS:")
    print(f"  Total Enrollments: {Enrollment.objects.count()}")
    
    # Check attendance
    print("\n✅ ATTENDANCE:")
    print(f"  Total Sessions: {AttendanceSession.objects.count()}")
    print(f"  Total Records: {AttendanceRecord.objects.count()}")
    
    # Check reports
    print("\n📊 REPORTS:")
    print(f"  Report Templates: {ReportTemplate.objects.count()}")
    print(f"  Dashboard Widgets: {DashboardWidget.objects.count()}")
    print(f"  Generated Reports: {GeneratedReport.objects.count()}")
    
    print("\n" + "=" * 50)
    print("✅ VERIFICATION COMPLETE")
    
    # Show sample login credentials
    print("\n🔐 SAMPLE LOGIN CREDENTIALS:")
    print("=" * 50)
    
    # Admin
    admin = User.objects.filter(user_type='admin').first()
    if admin:
        print(f"Admin: username='{admin.username}', password='admin123'")
    
    # Instructor
    instructor = User.objects.filter(user_type='instructor').first()
    if instructor:
        print(f"Instructor: username='{instructor.username}', password='instructor123'")
    
    # Student
    student_user = User.objects.filter(user_type='student').first()
    if student_user:
        try:
            student = student_user.student
            print(f"Student: username='{student_user.username}', password='student123'")
            print(f"         Admission No: {student.admission_number}")
        except:
            print(f"Student: username='{student_user.username}', password='student123'")

if __name__ == '__main__':
    verify_data()