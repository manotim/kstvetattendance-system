#!/usr/bin/env python
"""
Main data seeding script for TVET Attendance System
Run with: python manage.py shell < scripts/seed_data.py
"""

import os
import sys
import django
import random
from datetime import datetime, timedelta
from django.utils import timezone

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tvet_attendance.settings')
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import User
from courses.models import Course, Class
from students.models import Student, Enrollment, AcademicRecord
from attendance.models import AttendanceSession, AttendanceRecord, ExcuseApplication
from reports.models import ReportTemplate, DashboardWidget, GeneratedReport

def seed_accounts():
    """Seed user accounts with different roles"""
    print("Seeding accounts...")
    
    User = get_user_model()
    
    # Create super admin
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
        print(f"Created admin: {admin.username}")
    
    # Create instructors
    instructors_data = [
        {'username': 'instructor1', 'first_name': 'John', 'last_name': 'Kamau', 'email': 'john.kamau@tvet.ac.ke'},
        {'username': 'instructor2', 'first_name': 'Mary', 'last_name': 'Wanjiku', 'email': 'mary.wanjiku@tvet.ac.ke'},
        {'username': 'instructor3', 'first_name': 'Peter', 'last_name': 'Ochieng', 'email': 'peter.ochieng@tvet.ac.ke'},
        {'username': 'instructor4', 'first_name': 'Grace', 'last_name': 'Muthoni', 'email': 'grace.muthoni@tvet.ac.ke'},
    ]
    
    for data in instructors_data:
        instructor, created = User.objects.get_or_create(
            username=data['username'],
            defaults={
                'email': data['email'],
                'first_name': data['first_name'],
                'last_name': data['last_name'],
                'user_type': 'instructor',
                'department': 'Academic',
            }
        )
        if created:
            instructor.set_password('instructor123')
            instructor.save()
            print(f"Created instructor: {data['first_name']} {data['last_name']}")
    
    # Create registrar
    registrar, created = User.objects.get_or_create(
        username='registrar',
        defaults={
            'email': 'registrar@tvet.ac.ke',
            'first_name': 'Samuel',
            'last_name': 'Kibet',
            'user_type': 'registrar',
        }
    )
    if created:
        registrar.set_password('registrar123')
        registrar.save()
        print(f"Created registrar: {registrar.username}")
    
    # Create HOD
    hod, created = User.objects.get_or_create(
        username='hod',
        defaults={
            'email': 'hod@tvet.ac.ke',
            'first_name': 'Dr. Jane',
            'last_name': 'Atieno',
            'user_type': 'hod',
            'department': 'Computer Science',
        }
    )
    if created:
        hod.set_password('hod123')
        hod.save()
        print(f"Created HOD: {hod.username}")
    
    print(f"Total users created: {User.objects.count()}")
    return User.objects.all()

def seed_courses():
    """Seed courses and classes"""
    print("\nSeeding courses and classes...")
    
    # Create courses
    courses_data = [
        {
            'code': 'CS101',
            'name': 'Computer Science Fundamentals',
            'description': 'Introduction to computer science concepts, programming basics, and problem-solving techniques.',
            'level': 'certificate',
            'duration_months': 12,
            'department': 'Computer Science'
        },
        {
            'code': 'ENG201',
            'name': 'Electrical Engineering',
            'description': 'Fundamentals of electrical circuits, electronics, and power systems.',
            'level': 'diploma',
            'duration_months': 24,
            'department': 'Engineering'
        },
        {
            'code': 'BCT301',
            'name': 'Building Construction Technology',
            'description': 'Principles of building construction, materials, and site management.',
            'level': 'craft',
            'duration_months': 18,
            'department': 'Construction'
        },
        {
            'code': 'HOS401',
            'name': 'Hospitality Management',
            'description': 'Hotel operations, food service, and customer relations management.',
            'level': 'artisan',
            'duration_months': 9,
            'department': 'Hospitality'
        },
        {
            'code': 'AUT501',
            'name': 'Automotive Engineering',
            'description': 'Vehicle maintenance, repair, and diagnostics.',
            'level': 'craft',
            'duration_months': 18,
            'department': 'Engineering'
        },
    ]
    
    courses = []
    for data in courses_data:
        course, created = Course.objects.get_or_create(
            code=data['code'],
            defaults=data
        )
        if created:
            print(f"Created course: {course.code} - {course.name}")
        courses.append(course)
    
    # Create classes
    instructors = User.objects.filter(user_type='instructor')
    academic_years = ['2023/2024', '2024/2025']
    
    classes_data = []
    for course in courses:
        for year in academic_years:
            for semester in [1, 2]:
                class_code = f"{course.code}-{year.split('/')[0]}-S{semester}"
                classes_data.append({
                    'course': course,
                    'class_code': class_code,
                    'name': f"{course.name} - Semester {semester}",
                    'instructor': random.choice(instructors),
                    'academic_year': year,
                    'semester': semester,
                    'start_date': timezone.now().date() - timedelta(days=random.randint(30, 180)),
                    'end_date': timezone.now().date() + timedelta(days=random.randint(90, 270)),
                    'meeting_days': random.choice(['Monday, Wednesday', 'Tuesday, Thursday', 'Monday, Wednesday, Friday']),
                    'meeting_time': random.choice(['9:00 AM - 11:00 AM', '2:00 PM - 4:00 PM', '10:00 AM - 12:00 PM']),
                    'venue': random.choice(['Room 101', 'Lab A', 'Workshop 3', 'Hall B']),
                    'max_students': random.randint(25, 40),
                })
    
    created_classes = []
    for data in classes_data:
        class_obj, created = Class.objects.get_or_create(
            class_code=data['class_code'],
            defaults=data
        )
        if created:
            created_classes.append(class_obj)
            print(f"Created class: {class_obj.class_code}")
    
    print(f"Total courses: {Course.objects.count()}")
    print(f"Total classes: {Class.objects.count()}")
    return courses, created_classes

def seed_students():
    """Seed students and enrollments"""
    print("\nSeeding students...")
    
    # Student names (Kenyan names)
    first_names = [
        'Brian', 'Mercy', 'Kevin', 'Faith', 'David', 'Sarah', 'James', 'Linda', 
        'Michael', 'Esther', 'Daniel', 'Ruth', 'Joseph', 'Joy', 'Paul', 'Ann', 
        'Samuel', 'Mary', 'Peter', 'Grace', 'Simon', 'Jane', 'Isaac', 'Rose',
        'Victor', 'Susan', 'Collins', 'Irene', 'Mark', 'Agnes', 'Tony', 'Lucy',
        'Alex', 'Diana', 'Steve', 'Caroline', 'Ben', 'Naomi', 'Chris', 'Eunice'
    ]
    
    last_names = [
        'Mutua', 'Mwende', 'Kipchoge', 'Chebet', 'Omondi', 'Akinyi', 'Korir', 'Achieng',
        'Odhiambo', 'Atieno', 'Kiplagat', 'Jepchumba', 'Kiprono', 'Nyambura', 'Kamau', 'Wanjiru',
        'Njoroge', 'Wambui', 'Maina', 'Njeri', 'Kariuki', 'Wairimu', 'Mbugua', 'Nyokabi',
        'Gitau', 'Wanjiku', 'Waweru', 'Mumbi', 'Mwangi', 'Wangui', 'Kibe', 'Mueni',
        'Thuo', 'Waithera', 'Kinyua', 'Nyaguthii', 'Macharia', 'Wambugu', 'Gichuru', 'Karimi'
    ]
    
    counties = [
        'Kitui', 'Nairobi', 'Mombasa', 'Kisumu', 'Nakuru', 'Eldoret', 'Thika', 'Kitale',
        'Machakos', 'Meru', 'Kakamega', 'Bungoma', 'Busia', 'Siaya', 'Kisii', 'Nyamira'
    ]
    
    sub_counties = [
        'Central', 'West', 'East', 'North', 'South', 'Township', 'Rural', 'Urban'
    ]
    
    courses = Course.objects.all()
    
    students_created = 0
    students_list = []
    
    for i in range(100):  # Create 100 students
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        username = f"student_{first_name.lower()}_{last_name.lower()}_{i}"
        
        # Check if user exists
        if User.objects.filter(username=username).exists():
            continue
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=f"{first_name.lower()}.{last_name.lower()}{i}@student.tvet.ac.ke",
            first_name=first_name,
            last_name=last_name,
            user_type='student',
            password='student123',
        )
        
        # Create student profile
        student = Student.objects.create(
            user=user,
            date_of_birth=timezone.now().date() - timedelta(days=random.randint(18*365, 25*365)),
            gender=random.choice(['M', 'F']),
            address=f"P.O. Box {random.randint(1000, 9999)}",
            county=random.choice(counties),
            sub_county=random.choice(sub_counties),
            national_id=f"{random.randint(10000000, 99999999)}",
            emergency_contact_name=f"{random.choice(['Mr.', 'Mrs.'])} {random.choice(last_names)}",
            emergency_contact_phone=f"07{random.randint(10, 99)} {random.randint(100000, 999999)}",
            emergency_contact_relationship=random.choice(['Parent', 'Guardian', 'Sibling']),
            course=random.choice(courses),
            year_of_admission=random.randint(2022, 2024),
            status=random.choice(['active', 'active', 'active', 'inactive']),
            is_boarding=random.choice([True, False]),
            has_special_needs=random.choice([True, False, False, False]),
        )
        
        students_created += 1
        students_list.append(student)
        print(f"Created student: {student.admission_number} - {user.get_full_name()}")
    
    # Create enrollments
    print("\nCreating enrollments...")
    classes = Class.objects.filter(is_active=True)
    
    for student in students_list:
        # Enroll student in 1-3 random classes from their course
        student_classes = classes.filter(course=student.course).order_by('?')[:random.randint(1, 3)]
        
        for class_obj in student_classes:
            enrollment, created = Enrollment.objects.get_or_create(
                student=student,
                class_enrolled=class_obj,
                defaults={
                    'course': student.course,
                    'enrollment_type': random.choice(['regular', 'evening', 'weekend']),
                }
            )
            if created:
                print(f"Enrolled {student.admission_number} in {class_obj.class_code}")
    
    # Create academic records for some students
    print("\nCreating academic records...")
    for student in random.sample(students_list, 30):  # 30 random students
        for semester in [1, 2]:
            for module_num in range(1, 6):
                AcademicRecord.objects.create(
                    student=student,
                    module_code=f"{student.course.code[:3]}{module_num:03d}",
                    module_name=f"Module {module_num} - {student.course.name.split('-')[0]}",
                    grade=random.choice(['A', 'B', 'B', 'C', 'C', 'D']),
                    score=random.uniform(60, 95),
                    semester=semester,
                    academic_year='2023/2024',
                    remarks=random.choice(['Excellent', 'Good', 'Satisfactory', 'Needs improvement', ''])
                )
    
    print(f"Total students created: {students_created}")
    print(f"Total enrollments: {Enrollment.objects.count()}")
    print(f"Total academic records: {AcademicRecord.objects.count()}")
    
    return students_list

def seed_attendance():
    """Seed attendance data"""
    print("\nSeeding attendance data...")
    
    classes = Class.objects.filter(is_active=True)
    today = timezone.now().date()
    
    # Create attendance sessions for the past 30 days
    attendance_sessions = []
    for i in range(30):
        session_date = today - timedelta(days=i)
        
        # Skip weekends
        if session_date.weekday() >= 5:  # 5=Saturday, 6=Sunday
            continue
        
        for class_obj in random.sample(list(classes), random.randint(3, 6)):
            # Create attendance session
            session = AttendanceSession.objects.create(
                class_session=class_obj,
                instructor=class_obj.instructor,
                session_date=session_date,
                start_time=datetime.strptime(random.choice(['09:00', '10:00', '14:00', '15:00']), '%H:%M').time(),
                end_time=datetime.strptime(random.choice(['11:00', '12:00', '16:00', '17:00']), '%H:%M').time(),
                topic_covered=random.choice([
                    'Introduction to Programming',
                    'Electrical Circuits Basics',
                    'Building Materials',
                    'Customer Service',
                    'Engine Maintenance',
                    'Database Management',
                    'Network Security',
                    'Project Management'
                ]),
                venue=class_obj.venue,
                attendance_method=random.choice(['manual', 'qr_code', 'manual']),
                status='completed' if session_date < today else 'ongoing',
            )
            attendance_sessions.append(session)
            
            # Create attendance records for enrolled students
            enrollments = Enrollment.objects.filter(class_enrolled=class_obj, is_active=True)
            
            for enrollment in enrollments:
                # Determine attendance status with realistic probabilities
                rand = random.random()
                if rand < 0.75:  # 75% present
                    status = 'present'
                    check_in_time = timezone.make_aware(datetime.combine(
                        session_date,
                        session.start_time
                    )) + timedelta(minutes=random.randint(-10, 30))
                    
                    # 20% of present are late
                    if random.random() < 0.2:
                        status = 'late'
                        check_in_time = timezone.make_aware(datetime.combine(
                            session_date,
                            session.start_time
                        )) + timedelta(minutes=random.randint(10, 45))
                elif rand < 0.90:  # 15% absent
                    status = 'absent'
                    check_in_time = None
                else:  # 10% excused
                    status = 'absent'
                    check_in_time = None
                
                # Create attendance record
                AttendanceRecord.objects.create(
                    session=session,
                    student=enrollment.student,
                    status=status,
                    check_in_time=check_in_time,
                    marked_by=class_obj.instructor,
                    is_excused=(status == 'absent' and random.random() < 0.3),
                    excuse_reason=random.choice([
                        'Medical appointment',
                        'Family emergency',
                        'Transport issues',
                        'Official school activity',
                        ''
                    ]) if random.random() < 0.5 else '',
                    remarks=random.choice([
                        'Good participation',
                        'Asked relevant questions',
                        'Needs more practice',
                        'Completed assignment',
                        ''
                    ]) if status == 'present' else '',
                )
            
            # Update session statistics
            session.calculate_stats()
            
        if len(attendance_sessions) % 10 == 0:
            print(f"Created {len(attendance_sessions)} attendance sessions...")
    
    # Create excuse applications
    print("\nCreating excuse applications...")
    students = Student.objects.filter(status='active')[:20]  # 20 random students
    
    for student in students:
        classes = Class.objects.filter(enrollments__student=student, enrollments__is_active=True)
        if classes.exists():
            class_obj = random.choice(list(classes))
            
            excuse = ExcuseApplication.objects.create(
                student=student,
                class_session=class_obj,
                reason=random.choice([
                    'Medical treatment requiring hospitalization',
                    'Family wedding ceremony',
                    'National sports competition participation',
                    'Bereavement in the family',
                    'Official school representation'
                ]),
                start_date=today - timedelta(days=random.randint(1, 7)),
                end_date=today + timedelta(days=random.randint(1, 5)),
                status=random.choice(['pending', 'approved', 'rejected']),
            )
            
            if excuse.status == 'approved':
                excuse.reviewed_by = User.objects.filter(user_type='instructor').first()
                excuse.review_notes = 'Application reviewed and approved'
                excuse.reviewed_at = timezone.now()
                excuse.save()
    
    print(f"Total attendance sessions: {AttendanceSession.objects.count()}")
    print(f"Total attendance records: {AttendanceRecord.objects.count()}")
    print(f"Total excuse applications: {ExcuseApplication.objects.count()}")
    
    return attendance_sessions

def seed_reports():
    """Seed report templates and widgets"""
    print("\nSeeding reports data...")
    
    # Create report templates
    templates_data = [
        {
            'name': 'Daily Attendance Summary',
            'report_type': 'attendance_summary',
            'description': 'Daily summary of attendance across all classes',
            'parameters': {'group_by': 'day', 'include_charts': True}
        },
        {
            'name': 'Student Monthly Report',
            'report_type': 'student_attendance',
            'description': 'Monthly attendance report for individual students',
            'parameters': {'period': 'monthly', 'include_trends': True}
        },
        {
            'name': 'Class Performance Report',
            'report_type': 'class_attendance',
            'description': 'Class-wise attendance performance analysis',
            'parameters': {'include_comparison': True, 'include_student_list': True}
        },
        {
            'name': 'Instructor Performance',
            'report_type': 'instructor_report',
            'description': 'Attendance records managed by each instructor',
            'parameters': {'group_by': 'instructor', 'include_metrics': True}
        },
    ]
    
    admin_user = User.objects.filter(user_type='admin').first()
    
    for data in templates_data:
        template, created = ReportTemplate.objects.get_or_create(
            name=data['name'],
            defaults={
                'report_type': data['report_type'],
                'description': data['description'],
                'parameters': data['parameters'],
                'created_by': admin_user,
            }
        )
        if created:
            print(f"Created report template: {template.name}")
    
    # Create dashboard widgets
    widgets_data = [
        {
            'name': 'Today\'s Attendance',
            'widget_type': 'attendance_chart',
            'chart_type': 'doughnut',
            'description': 'Shows today\'s attendance statistics',
            'configuration': {'refresh_interval': 15},
            'width': 4,
            'height': 300,
            'user_types': ['admin', 'instructor', 'registrar', 'hod']
        },
        {
            'name': 'Student Statistics',
            'widget_type': 'student_stats',
            'description': 'Overall student statistics and demographics',
            'configuration': {'show_gender_distribution': True},
            'width': 4,
            'height': 300,
            'user_types': ['admin', 'registrar', 'hod']
        },
        {
            'name': 'Class Overview',
            'widget_type': 'class_stats',
            'description': 'Active classes and their statistics',
            'configuration': {'max_items': 5},
            'width': 4,
            'height': 300,
            'user_types': ['admin', 'instructor', 'hod']
        },
        {
            'name': 'Attendance Trends',
            'widget_type': 'attendance_chart',
            'chart_type': 'line',
            'description': 'Weekly attendance trends',
            'configuration': {'period': 'week', 'show_comparison': True},
            'width': 6,
            'height': 350,
            'user_types': ['admin', 'instructor', 'hod']
        },
        {
            'name': 'Recent Activity',
            'widget_type': 'recent_activity',
            'description': 'Recent attendance sessions and updates',
            'configuration': {'max_items': 8},
            'width': 6,
            'height': 350,
            'user_types': ['admin', 'instructor']
        },
        {
            'name': 'Quick Actions',
            'widget_type': 'quick_links',
            'description': 'Quick access to common actions',
            'configuration': {'links': ['mark_attendance', 'view_reports', 'add_student']},
            'width': 12,
            'height': 150,
            'user_types': ['admin', 'instructor', 'student', 'registrar', 'hod']
        },
    ]
    
    for i, data in enumerate(widgets_data):
        widget, created = DashboardWidget.objects.get_or_create(
            name=data['name'],
            defaults={
                'widget_type': data['widget_type'],
                'chart_type': data.get('chart_type'),
                'description': data['description'],
                'configuration': data['configuration'],
                'width': data['width'],
                'height': data['height'],
                'display_order': i,
                'user_types': data['user_types'],
            }
        )
        if created:
            print(f"Created dashboard widget: {widget.name}")
    
    # Create sample generated reports
    print("\nCreating sample generated reports...")
    
    for i in range(5):
        report_date = timezone.now().date() - timedelta(days=i*7)
        
        GeneratedReport.objects.create(
            report_name=f'Weekly Attendance Report - {report_date.strftime("%d/%m/%Y")}',
            report_type='attendance_summary',
            description=f'Weekly attendance summary for the week ending {report_date.strftime("%d/%m/%Y")}',
            parameters={'period': 'weekly', 'group_by': 'class'},
            start_date=report_date - timedelta(days=6),
            end_date=report_date,
            data={
                'total_sessions': random.randint(40, 60),
                'total_present': random.randint(800, 1000),
                'total_absent': random.randint(50, 100),
                'attendance_rate': random.uniform(85, 95),
                'top_classes': [
                    {'class': 'CS101-2024-S1', 'rate': 92.5},
                    {'class': 'ENG201-2024-S1', 'rate': 89.2},
                    {'class': 'BCT301-2024-S1', 'rate': 87.8},
                ]
            },
            summary={
                'attendance_rate': random.uniform(85, 95),
                'punctuality_rate': random.uniform(80, 90),
                'improvement': random.uniform(-5, 5),
            },
            file_format=random.choice(['pdf', 'excel']),
            generated_by=admin_user,
            is_ready=True,
        )
    
    print(f"Total report templates: {ReportTemplate.objects.count()}")
    print(f"Total dashboard widgets: {DashboardWidget.objects.count()}")
    print(f"Total generated reports: {GeneratedReport.objects.count()}")

def main():
    """Main function to run all seeding scripts"""
    print("=" * 60)
    print("TVET ATTENDANCE SYSTEM - DATA SEEDING SCRIPT")
    print("=" * 60)
    
    try:
        # Seed in order
        users = seed_accounts()
        courses, classes = seed_courses()
        students = seed_students()
        attendance_sessions = seed_attendance()
        reports = seed_reports()
        
        print("\n" + "=" * 60)
        print("SEEDING COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
        # Print summary
        from django.db.models import Count
        
        print("\nDATABASE SUMMARY:")
        print(f"📊 Total Users: {User.objects.count()}")
        print(f"📚 Total Courses: {Course.objects.count()}")
        print(f"🏫 Total Classes: {Class.objects.count()}")
        print(f"👨‍🎓 Total Students: {Student.objects.count()}")
        print(f"📝 Total Enrollments: {Enrollment.objects.count()}")
        print(f"✅ Total Attendance Sessions: {AttendanceSession.objects.count()}")
        print(f"📋 Total Attendance Records: {AttendanceRecord.objects.count()}")
        
        # Print login credentials
        print("\n🔐 TEST LOGIN CREDENTIALS:")
        print("Admin: username='admin', password='admin123'")
        print("Instructor: username='instructor1', password='instructor123'")
        print("Student: username='student_brian_mutua_0', password='student123'")
        print("Registrar: username='registrar', password='registrar123'")
        print("HOD: username='hod', password='hod123'")
        
        print("\n🚀 Seeding completed! Start the server with: python manage.py runserver")
        
    except Exception as e:
        print(f"\n❌ ERROR during seeding: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()