# management/commands/setup_instructor_permissions.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from accounts.models import User
from students.models import Student, Enrollment
from attendance.models import AttendanceSession, AttendanceRecord

class Command(BaseCommand):
    help = 'Set up instructor permissions for student management'

    def handle(self, *args, **options):
        # Create or get instructor group
        instructor_group, created = Group.objects.get_or_create(name='Instructors')
        
        if created:
            self.stdout.write(self.style.SUCCESS('Created Instructors group'))
        
        # Clear existing permissions to avoid duplicates
        instructor_group.permissions.clear()
        
        # Get content types
        student_ct = ContentType.objects.get_for_model(Student)
        enrollment_ct = ContentType.objects.get_for_model(Enrollment)
        session_ct = ContentType.objects.get_for_model(AttendanceSession)
        record_ct = ContentType.objects.get_for_model(AttendanceRecord)
        
        # Student permissions - instructors need full CRUD for students
        student_perms = Permission.objects.filter(
            content_type=student_ct,
            codename__in=['add_student', 'change_student', 'view_student', 'delete_student']
        )
        instructor_group.permissions.add(*student_perms)
        
        # Enrollment permissions
        enrollment_perms = Permission.objects.filter(
            content_type=enrollment_ct,
            codename__in=['add_enrollment', 'change_enrollment', 'view_enrollment', 'delete_enrollment']
        )
        instructor_group.permissions.add(*enrollment_perms)
        
        # Attendance session permissions
        session_perms = Permission.objects.filter(
            content_type=session_ct,
            codename__in=['add_attendancesession', 'change_attendancesession', 
                         'view_attendancesession', 'delete_attendancesession']
        )
        instructor_group.permissions.add(*session_perms)
        
        # Attendance record permissions
        record_perms = Permission.objects.filter(
            content_type=record_ct,
            codename__in=['add_attendancerecord', 'change_attendancerecord', 
                         'view_attendancerecord', 'delete_attendancerecord']
        )
        instructor_group.permissions.add(*record_perms)
        
        # Add all instructors to the group
        instructors = User.objects.filter(user_type='instructor')
        count = 0
        for instructor in instructors:
            instructor.groups.add(instructor_group)
            count += 1
        
        self.stdout.write(self.style.SUCCESS(
            f'Successfully added {count} instructors to Instructors group with full student management permissions'
        ))