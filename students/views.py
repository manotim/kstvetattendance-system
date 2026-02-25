# students/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
import csv
from io import TextIOWrapper

from .models import Student, Enrollment, AcademicRecord
from .forms import StudentRegistrationForm, StudentUpdateForm, EnrollmentForm, BulkStudentImportForm
from accounts.models import User
from courses.models import Class 
from attendance.models import AttendanceSession, AttendanceRecord, AttendanceSummary
from datetime import timedelta

@login_required
def student_list(request):
    query = request.GET.get('q', '')
    status = request.GET.get('status', '')
    course = request.GET.get('course', '')
    
    students = Student.objects.select_related('user', 'course').all()
    
    if query:
        students = students.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(admission_number__icontains=query) |
            Q(national_id__icontains=query) |
            Q(user__email__icontains=query)
        )
    
    if status:
        students = students.filter(status=status)
    
    if course:
        students = students.filter(course_id=course)
    
    # Pagination
    paginator = Paginator(students.order_by('admission_number'), 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'query': query,
        'status': status,
        'course': course,
        'total_students': students.count(),
    }
    return render(request, 'students/student_list.html', context)

@login_required
def student_detail(request, pk):
    student = get_object_or_404(Student.objects.select_related('user', 'course', 'current_class'), pk=pk)
    enrollments = student.enrollments.select_related('course', 'class_enrolled').all()
    academic_records = student.academic_records.all()
    
    context = {
        'student': student,
        'enrollments': enrollments,
        'academic_records': academic_records,
    }
    return render(request, 'students/student_detail.html', context)

@login_required
@permission_required('students.add_student', raise_exception=True)
def student_register(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Student {user.get_full_name()} registered successfully!')
            return redirect('students:detail', pk=user.student.pk)
    else:
        form = StudentRegistrationForm()
    
    context = {'form': form}
    return render(request, 'students/student_register.html', context)

@login_required
def student_update(request, pk):
    student = get_object_or_404(Student, pk=pk)
    
    if request.method == 'POST':
        form = StudentUpdateForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, 'Student information updated successfully!')
            return redirect('students:detail', pk=pk)
    else:
        form = StudentUpdateForm(instance=student)
    
    context = {
        'form': form,
        'student': student,
    }
    return render(request, 'students/student_update.html', context)

@login_required
@permission_required('students.add_enrollment', raise_exception=True)
def enroll_student(request, student_pk):
    student = get_object_or_404(Student, pk=student_pk)
    
    if request.method == 'POST':
        form = EnrollmentForm(request.POST, student=student)
        if form.is_valid():
            enrollment = form.save(commit=False)
            enrollment.student = student
            enrollment.save()
            messages.success(request, 'Student enrolled successfully!')
            return redirect('students:detail', pk=student_pk)
    else:
        form = EnrollmentForm(student=student)
    
    context = {
        'form': form,
        'student': student,
    }
    return render(request, 'students/enroll_student.html', context)

@login_required
@permission_required('students.add_student', raise_exception=True)
def bulk_import_students(request):
    if request.method == 'POST':
        form = BulkStudentImportForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            
            # Read CSV file
            csv_file = TextIOWrapper(csv_file.file, encoding='utf-8')
            reader = csv.DictReader(csv_file)
            
            imported = 0
            errors = []
            
            for row_num, row in enumerate(reader, start=2):  # start=2 for header row
                try:
                    # Create user
                    username = f"student_{row['first_name'].lower()}_{row['last_name'].lower()}"
                    if User.objects.filter(username=username).exists():
                        username = f"{username}_{row_num}"
                    
                    user = User.objects.create_user(
                        username=username,
                        email=row.get('email', ''),
                        first_name=row['first_name'],
                        last_name=row['last_name'],
                        user_type='student',
                        password='tvet123'  # Default password
                    )
                    
                    # Create student
                    Student.objects.create(
                        user=user,
                        date_of_birth=row['date_of_birth'],
                        gender=row['gender'],
                        address=row['address'],
                        county=row.get('county', 'Kitui'),
                        sub_county=row.get('sub_county', ''),
                        national_id=row.get('national_id', ''),
                        emergency_contact_name=row.get('emergency_contact_name', ''),
                        emergency_contact_phone=row.get('emergency_contact_phone', ''),
                        emergency_contact_relationship=row.get('emergency_contact_relationship', 'Parent'),
                    )
                    
                    imported += 1
                    
                except Exception as e:
                    errors.append(f"Row {row_num}: {str(e)}")
            
            if imported > 0:
                messages.success(request, f'Successfully imported {imported} students!')
            if errors:
                messages.warning(request, f'Some errors occurred: {", ".join(errors[:5])}')
            
            return redirect('students:list')
    else:
        form = BulkStudentImportForm()
    
    context = {'form': form}
    return render(request, 'students/bulk_import.html', context)

@login_required
def student_dashboard(request):
    if request.user.user_type != 'student':
        return redirect('dashboard')
    
    try:
        student = request.user.student
    except Student.DoesNotExist:
        return redirect('logout')
    
    enrollments = student.enrollments.select_related('course', 'class_enrolled').filter(is_active=True)
    academic_records = student.academic_records.all()[:5]
    
    context = {
        'student': student,
        'enrollments': enrollments,
        'academic_records': academic_records,
    }
    return render(request, 'students/student_dashboard.html', context)

@require_POST
@login_required
@permission_required('students.change_student', raise_exception=True)
def toggle_student_status(request, pk):
    student = get_object_or_404(Student, pk=pk)
    
    if student.status == 'active':
        student.status = 'inactive'
        message = f'Student {student.admission_number} deactivated.'
    else:
        student.status = 'active'
        message = f'Student {student.admission_number} activated.'
    
    student.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'message': message,
            'new_status': student.status,
            'new_status_display': student.get_status_display()
        })
    
    messages.success(request, message)
    return redirect('students:detail', pk=pk)

@login_required
def students_by_class(request, class_id):
    """
    View to display all students enrolled in a specific class
    """
    # Get the class
    class_obj = get_object_or_404(Class, pk=class_id)
    
    # Get filter parameters
    query = request.GET.get('q', '')
    gender = request.GET.get('gender', '')
    status = request.GET.get('status', '')
    
    # Base queryset for enrollments
    enrollments = Enrollment.objects.filter(
        class_enrolled=class_obj,
        is_active=True
    ).select_related(
        'student', 
        'student__user', 
        'course'
    ).prefetch_related(
        'student__attendance_records',
        'student__attendance_summaries'
    )
    
    # Apply filters
    if query:
        enrollments = enrollments.filter(
            Q(student__user__first_name__icontains=query) |
            Q(student__user__last_name__icontains=query) |
            Q(student__admission_number__icontains=query) |
            Q(student__national_id__icontains=query) |
            Q(student__user__email__icontains=query)
        )
    
    if gender:
        enrollments = enrollments.filter(student__gender=gender)
    
    if status:
        enrollments = enrollments.filter(student__status=status)
    
    # Get today's date
    today = timezone.now().date()
    current_month = today.month
    current_year = today.year
    
    # Calculate attendance statistics for each enrollment
    for enrollment in enrollments:
        student = enrollment.student
        
        # Get total sessions for this course in current month
        total_sessions = AttendanceSession.objects.filter(
            class_session=class_obj,
            session_date__month=current_month,
            session_date__year=current_year,
            status='completed'
        ).count()
        
        # Get attendance records for this student in current month
        attendance_records = AttendanceRecord.objects.filter(
            student=student,
            session__class_session=class_obj,
            session__session_date__month=current_month,
            session__session_date__year=current_year
        )
        
        # Calculate statistics
        if total_sessions > 0:
            attended = attendance_records.filter(status='present').count()
            late = attendance_records.filter(status='late').count()
            absent = attendance_records.filter(status='absent').count()
            excused = attendance_records.filter(status='excused').count()
            half_day = attendance_records.filter(status='half_day').count()
            
            # Calculate attendance percentage
            total_present_weighted = attended + (half_day * 0.5)  # Half day counts as 0.5
            enrollment.attendance_percentage = round((total_present_weighted / total_sessions) * 100, 1)
            
            # Calculate punctuality rate (percentage of times student was on time when present)
            total_present_actual = attended + half_day
            if total_present_actual > 0:
                enrollment.punctuality_rate = round(((total_present_actual - late) / total_present_actual) * 100, 1)
            else:
                enrollment.punctuality_rate = 0
                
            # Store other stats
            enrollment.late_count = late
            enrollment.absent_count = absent
            enrollment.excused_count = excused
            enrollment.half_day_count = half_day
        else:
            enrollment.attendance_percentage = 0
            enrollment.punctuality_rate = 0
            enrollment.late_count = 0
            enrollment.absent_count = 0
            enrollment.excused_count = 0
            enrollment.half_day_count = 0
        
        # Get last attendance date
        last_attendance = attendance_records.filter(
            status__in=['present', 'late', 'half_day']
        ).order_by('-session__session_date').first()
        
        if last_attendance:
            enrollment.last_attendance_date = last_attendance.session.session_date
        else:
            enrollment.last_attendance_date = None
        
        # Get attendance summary if exists
        try:
            summary = AttendanceSummary.objects.get(
                student=student,
                class_session=class_obj,
                period_type='monthly',
                period_start__month=current_month,
                period_start__year=current_year
            )
            enrollment.summary = summary
        except AttendanceSummary.DoesNotExist:
            enrollment.summary = None
    
    # Statistics for the class
    total_students = enrollments.count()
    
    # Today's attendance
    today_sessions = AttendanceSession.objects.filter(
        class_session=class_obj,
        session_date=today,
        status='completed'
    )
    
    if today_sessions.exists():
        today_session = today_sessions.first()
        present_today = today_session.total_present
        late_today = today_session.total_late
        absent_today = today_session.total_absent
    else:
        present_today = 0
        late_today = 0
        absent_today = 0
    
    # Gender counts
    male_count = enrollments.filter(student__gender='male').count()
    female_count = enrollments.filter(student__gender='female').count()
    other_count = enrollments.filter(student__gender='other').count()
    
    # Calculate average attendance for the class
    total_attendance_percentage = 0
    total_punctuality = 0
    students_with_attendance = 0
    
    for enrollment in enrollments:
        if enrollment.attendance_percentage > 0:
            total_attendance_percentage += enrollment.attendance_percentage
            total_punctuality += enrollment.punctuality_rate
            students_with_attendance += 1
    
    avg_attendance = round(total_attendance_percentage / students_with_attendance, 1) if students_with_attendance > 0 else 0
    avg_punctuality = round(total_punctuality / students_with_attendance, 1) if students_with_attendance > 0 else 0
    
    # Get recent attendance sessions for this class
    recent_sessions = AttendanceSession.objects.filter(
        class_session=class_obj,
        status='completed'
    ).order_by('-session_date', '-start_time')[:5]
    
    # Get attendance trends (last 5 days)
    trend_data = []
    for i in range(5):
        date = today - timedelta(days=i)
        sessions_on_date = AttendanceSession.objects.filter(
            class_session=class_obj,
            session_date=date,
            status='completed'
        )
        
        if sessions_on_date.exists():
            total_present = sum(session.total_present for session in sessions_on_date)
            total_students_on_date = total_students  # You might want to adjust this for historical data
            attendance_rate = round((total_present / total_students_on_date) * 100, 1) if total_students_on_date > 0 else 0
        else:
            attendance_rate = None
            
        trend_data.append({
            'date': date.strftime('%a, %b %d'),
            'rate': attendance_rate
        })
    
    # Pagination
    paginator = Paginator(enrollments, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'class_obj': class_obj,
        'enrollments': page_obj,
        'total_students': total_students,
        'present_today': present_today,
        'late_today': late_today,
        'absent_today': absent_today,
        'male_count': male_count,
        'female_count': female_count,
        'other_count': other_count,
        'avg_attendance': avg_attendance,
        'avg_punctuality': avg_punctuality,
        'recent_sessions': recent_sessions,
        'trend_data': trend_data,
        'query': query,
        'gender': gender,
        'status': status,
        'is_paginated': paginator.num_pages > 1,
        'page_obj': page_obj,
        'today': today,
    }
    
    return render(request, 'students/students_by_class.html', context)