# courses/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from attendance.models import AttendanceRecord, AttendanceSession
from django.http import JsonResponse
from attendance.models import AttendanceRecord
from .models import Course, Class
from .forms import CourseForm, ClassForm, ClassEnrollmentForm
from students.models import Enrollment, Student
from accounts.models import User

@login_required
def course_list(request):
    """List all courses"""
    query = request.GET.get('q', '')
    level = request.GET.get('level', '')
    department = request.GET.get('department', '')
    
    courses = Course.objects.all()
    
    if query:
        courses = courses.filter(
            Q(code__icontains=query) |
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )
    
    if level:
        courses = courses.filter(level=level)
    
    if department:
        courses = courses.filter(department__icontains=department)
    
    # Get statistics
    total_courses = courses.count()
    active_courses = courses.filter(is_active=True).count()
    
    # Get unique departments for filter
    departments = Course.objects.values_list('department', flat=True).distinct()
    
    # Pagination
    paginator = Paginator(courses.order_by('code'), 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'query': query,
        'level': level,
        'department': department,
        'departments': departments,
        'total_courses': total_courses,
        'active_courses': active_courses,
        'level_choices': Course.LEVEL_CHOICES,
    }
    return render(request, 'courses/course_list.html', context)

@login_required
def course_detail(request, pk):
    """View course details"""
    course = get_object_or_404(Course.objects.prefetch_related('classes'), pk=pk)
    active_classes = course.classes.filter(is_active=True)
    total_students = Student.objects.filter(course=course, status='active').count()
    
    context = {
        'course': course,
        'active_classes': active_classes,
        'total_students': total_students,
    }
    return render(request, 'courses/course_detail.html', context)

@login_required
@permission_required('courses.add_course', raise_exception=True)
def course_create(request):
    """Create a new course"""
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save()
            messages.success(request, f'Course {course.code} created successfully!')
            return redirect('courses:detail', pk=course.pk)
    else:
        form = CourseForm()
    
    context = {'form': form}
    return render(request, 'courses/course_form.html', context)

@login_required
@permission_required('courses.change_course', raise_exception=True)
def course_update(request, pk):
    """Update a course"""
    course = get_object_or_404(Course, pk=pk)
    
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, f'Course {course.code} updated successfully!')
            return redirect('courses:detail', pk=course.pk)
    else:
        form = CourseForm(instance=course)
    
    context = {'form': form, 'course': course}
    return render(request, 'courses/course_form.html', context)

@login_required
@permission_required('courses.delete_course', raise_exception=True)
def course_delete(request, pk):
    """Delete a course (soft delete by deactivating)"""
    course = get_object_or_404(Course, pk=pk)
    
    if request.method == 'POST':
        course.is_active = False
        course.save()
        messages.success(request, f'Course {course.code} has been deactivated.')
        return redirect('courses:list')
    
    context = {'course': course}
    return render(request, 'courses/course_confirm_delete.html', context)

@login_required
def class_list(request):
    """List all classes"""
    query = request.GET.get('q', '')
    course_id = request.GET.get('course', '')
    academic_year = request.GET.get('academic_year', '')
    semester = request.GET.get('semester', '')
    
    classes = Class.objects.select_related('course', 'instructor').all()
    
    if query:
        classes = classes.filter(
            Q(class_code__icontains=query) |
            Q(name__icontains=query) |
            Q(venue__icontains=query)
        )
    
    if course_id:
        classes = classes.filter(course_id=course_id)
    
    if academic_year:
        classes = classes.filter(academic_year=academic_year)
    
    if semester:
        classes = classes.filter(semester=semester)
    
    # Get statistics
    total_classes = classes.count()
    active_classes = classes.filter(is_active=True).count()
    
    # Get unique academic years for filter
    academic_years = Class.objects.values_list('academic_year', flat=True).distinct().order_by('-academic_year')
    
    # Pagination
    paginator = Paginator(classes.order_by('-academic_year', 'semester', 'class_code'), 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'query': query,
        'course_id': course_id,
        'academic_year': academic_year,
        'semester': semester,
        'academic_years': academic_years,
        'courses': Course.objects.filter(is_active=True),
        'total_classes': total_classes,
        'active_classes': active_classes,
    }
    return render(request, 'courses/class_list.html', context)

@login_required
def class_detail(request, pk):
    """View class details"""
    class_obj = get_object_or_404(
        Class.objects.select_related('course', 'instructor'),
        pk=pk
    )
    
    # Get enrolled students
    enrollments = class_obj.enrollments.filter(is_active=True).select_related('student', 'student__user')
    
    # Get attendance statistics
    from attendance.models import AttendanceSession
    total_sessions = AttendanceSession.objects.filter(class_session=class_obj).count()
    upcoming_sessions = AttendanceSession.objects.filter(
        class_session=class_obj,
        status='scheduled'
    ).order_by('session_date', 'start_time')[:5]
    
    context = {
        'class': class_obj,
        'enrollments': enrollments,
        'total_students': enrollments.count(),
        'total_sessions': total_sessions,
        'upcoming_sessions': upcoming_sessions,
    }
    return render(request, 'courses/class_detail.html', context)

@login_required
@permission_required('courses.add_class', raise_exception=True)
def class_create(request):
    """Create a new class"""
    if request.method == 'POST':
        form = ClassForm(request.POST)
        if form.is_valid():
            class_obj = form.save()
            messages.success(request, f'Class {class_obj.class_code} created successfully!')
            return redirect('courses:class_detail', pk=class_obj.pk)
    else:
        form = ClassForm()
    
    context = {'form': form}
    return render(request, 'courses/class_form.html', context)

@login_required
@permission_required('courses.change_class', raise_exception=True)
def class_update(request, pk):
    """Update a class"""
    class_obj = get_object_or_404(Class, pk=pk)
    
    if request.method == 'POST':
        form = ClassForm(request.POST, instance=class_obj)
        if form.is_valid():
            form.save()
            messages.success(request, f'Class {class_obj.class_code} updated successfully!')
            return redirect('courses:class_detail', pk=class_obj.pk)
    else:
        form = ClassForm(instance=class_obj)
    
    context = {'form': form, 'class': class_obj}
    return render(request, 'courses/class_form.html', context)

@login_required
@permission_required('courses.delete_class', raise_exception=True)
def class_delete(request, pk):
    """Delete a class (soft delete by deactivating)"""
    class_obj = get_object_or_404(Class, pk=pk)
    
    if request.method == 'POST':
        class_obj.is_active = False
        class_obj.save()
        messages.success(request, f'Class {class_obj.class_code} has been deactivated.')
        return redirect('courses:class_list')
    
    context = {'class': class_obj}
    return render(request, 'courses/class_confirm_delete.html', context)

@login_required
@permission_required('students.add_enrollment', raise_exception=True)
def enroll_students(request, class_id):
    """Enroll students in a class"""
    class_obj = get_object_or_404(Class, pk=class_id)
    
    if request.method == 'POST':
        form = ClassEnrollmentForm(request.POST, class_obj=class_obj)
        if form.is_valid():
            students = form.cleaned_data['students']
            enrolled_count = 0
            
            for student in students:
                # Check if student is already enrolled
                if not Enrollment.objects.filter(student=student, class_enrolled=class_obj).exists():
                    Enrollment.objects.create(
                        student=student,
                        course=class_obj.course,
                        class_enrolled=class_obj,
                        enrollment_type='regular'
                    )
                    enrolled_count += 1
            
            messages.success(request, f'{enrolled_count} students enrolled in {class_obj.class_code}')
            return redirect('courses:class_detail', pk=class_id)
    else:
        form = ClassEnrollmentForm(class_obj=class_obj)
    
    context = {
        'form': form,
        'class': class_obj,
    }
    return render(request, 'courses/enroll_students.html', context)

@login_required
def instructor_classes(request):
    """View for instructors to see their assigned classes"""
    if request.user.user_type != 'instructor':
        messages.error(request, "Access denied. Instructors only.")
        return redirect('dashboard')
    
    # Get classes taught by this instructor
    classes = Class.objects.filter(
        instructor=request.user,
        is_active=True
    ).select_related('course').prefetch_related('enrollments')
    
    # Add additional data to each class
    from django.utils import timezone
    today = timezone.now().date()
    
    for class_obj in classes:
        # Count students
        class_obj.student_count = class_obj.enrollments.filter(is_active=True).count()
        
        # Check if there's a session today
        class_obj.today_session = class_obj.attendance_sessions.filter(
            session_date=today
        ).exists()
        
        # Get total sessions
        class_obj.total_sessions = class_obj.attendance_sessions.count()
        
        # Get next session
        next_session = class_obj.attendance_sessions.filter(
            session_date__gte=today
        ).order_by('session_date', 'start_time').first()
        class_obj.next_session = next_session
        
        # Calculate attendance rate (optional)
        if class_obj.total_sessions > 0:
            total_records = AttendanceRecord.objects.filter(
                session__class_session=class_obj
            ).count()
            present_records = AttendanceRecord.objects.filter(
                session__class_session=class_obj,
                status='present'
            ).count()
            class_obj.attendance_rate = round((present_records / total_records) * 100, 1) if total_records > 0 else 0
        else:
            class_obj.attendance_rate = 0
    
    context = {
        'classes': classes,
    }
    return render(request, 'courses/instructor_classes.html', context)


@login_required
def student_classes(request):
    """View for students to see their enrolled classes"""
    # Check if user is a student
    if request.user.user_type != 'student':
        return redirect('dashboard')
    
    try:
        student = request.user.student
        
        # Get active enrollments
        enrollments = Enrollment.objects.filter(
            student=student,
            is_active=True
        ).select_related('class_enrolled', 'course', 'class_enrolled__instructor')
        
        # Calculate attendance for each enrollment
        total_attendance = 0
        for enrollment in enrollments:
            # Get attendance records for this class
            attendance_records = AttendanceRecord.objects.filter(
                student=student,
                session__class_session=enrollment.class_enrolled
            )
            
            # Calculate counts
            enrollment.present_count = attendance_records.filter(status='present').count()
            enrollment.late_count = attendance_records.filter(status='late').count()
            enrollment.absent_count = attendance_records.filter(status='absent').count()
            
            total_sessions = attendance_records.count()
            if total_sessions > 0:
                enrollment.attendance_percentage = round(
                    (enrollment.present_count + enrollment.late_count) / total_sessions * 100, 1
                )
            else:
                enrollment.attendance_percentage = 0
            
            # Get next session
            enrollment.next_session = AttendanceSession.objects.filter(
                class_session=enrollment.class_enrolled,
                session_date__gte=timezone.now().date(),
                status='scheduled'
            ).order_by('session_date', 'start_time').first()
            
            total_attendance += enrollment.attendance_percentage
        
        # Calculate average attendance
        avg_attendance = round(total_attendance / len(enrollments), 1) if enrollments else 0
        
        # Count upcoming sessions
        upcoming_sessions = AttendanceSession.objects.filter(
            class_session__in=[e.class_enrolled for e in enrollments],
            session_date__gte=timezone.now().date(),
            status='scheduled'
        ).count()
        
        context = {
            'enrollments': enrollments,
            'avg_attendance': avg_attendance,
            'upcoming_sessions': upcoming_sessions,
        }
        
    except Student.DoesNotExist:
        context = {
            'enrollments': [],
            'avg_attendance': 0,
            'upcoming_sessions': 0,
        }
    
    return render(request, 'courses/student_classes.html', context)

# courses/views.py
from django.contrib.admin.views.decorators import staff_member_required

@login_required
@staff_member_required  # Only admin/staff can access
def manage_instructor_assignments(request):
    """
    Admin view to manage instructor assignments to classes
    """
    # Get filter parameters
    instructor_id = request.GET.get('instructor')
    course_id = request.GET.get('course')
    academic_year = request.GET.get('academic_year')
    
    # Base queryset
    classes = Class.objects.select_related('course', 'instructor').all()
    
    # Apply filters
    if instructor_id:
        classes = classes.filter(instructor_id=instructor_id)
    if course_id:
        classes = classes.filter(course_id=course_id)
    if academic_year:
        classes = classes.filter(academic_year=academic_year)
    
    # Get all instructors for filter dropdown
    instructors = User.objects.filter(user_type='instructor', is_active=True)
    courses = Course.objects.filter(is_active=True)
    academic_years = Class.objects.values_list('academic_year', flat=True).distinct().order_by('-academic_year')
    
    # Unassigned classes
    unassigned_classes = classes.filter(instructor__isnull=True)
    
    # Classes by instructor (only assigned ones)
    instructor_classes = {}
    for instructor in instructors:
        assigned = classes.filter(instructor=instructor)
        if assigned.exists():
            instructor_classes[instructor] = assigned
    
    context = {
        'instructors': instructors,
        'courses': courses,
        'academic_years': academic_years,
        'instructor_classes': instructor_classes,
        'unassigned_classes': unassigned_classes,
        'total_classes': classes.count(),
        'assigned_count': classes.filter(instructor__isnull=False).count(),
        'unassigned_count': unassigned_classes.count(),
    }
    return render(request, 'courses/manage_instructor_assignments.html', context)

@login_required
@staff_member_required
def bulk_assign_instructors(request):
    """
    Bulk assign instructors to multiple classes
    """
    if request.method == 'POST':
        instructor_id = request.POST.get('instructor')
        class_ids = request.POST.getlist('class_ids')
        
        if instructor_id and class_ids:
            instructor = get_object_or_404(User, id=instructor_id, user_type='instructor')
            updated = Class.objects.filter(id__in=class_ids).update(instructor=instructor)
            messages.success(request, f'Successfully assigned {instructor.get_full_name()} to {updated} classes')
        else:
            messages.warning(request, 'Please select both an instructor and at least one class')
        
        return redirect('courses:manage_instructor_assignments')
    
    return redirect('courses:manage_instructor_assignments')


@login_required
@staff_member_required
def assign_instructor_to_class(request, class_id):
    """
    Assign or change instructor for a specific class
    """
    class_obj = get_object_or_404(Class, id=class_id)
    
    if request.method == 'POST':
        instructor_id = request.POST.get('instructor')
        if instructor_id:
            instructor = get_object_or_404(User, id=instructor_id, user_type='instructor')
            class_obj.instructor = instructor
            class_obj.save()
            messages.success(request, f'Instructor {instructor.get_full_name()} assigned to {class_obj.class_code}')
        else:
            class_obj.instructor = None
            class_obj.save()
            messages.success(request, f'Instructor removed from {class_obj.class_code}')
        
        return redirect('courses:manage_instructor_assignments')
    
    # GET request - show assignment form (if accessed directly)
    return redirect('courses:manage_instructor_assignments')


# courses/views.py - Add these at the bottom of the file

from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q
from accounts.models import User

@login_required
@staff_member_required
def manage_instructor_assignments(request):
    """
    Admin view to manage instructor assignments to classes
    """
    # Get filter parameters
    instructor_id = request.GET.get('instructor')
    course_id = request.GET.get('course')
    academic_year = request.GET.get('academic_year')
    
    # Base queryset
    classes = Class.objects.select_related('course', 'instructor').all()
    
    # Apply filters
    if instructor_id:
        classes = classes.filter(instructor_id=instructor_id)
    if course_id:
        classes = classes.filter(course_id=course_id)
    if academic_year:
        classes = classes.filter(academic_year=academic_year)
    
    # Get all instructors for filter dropdown
    instructors = User.objects.filter(user_type='instructor', is_active=True)
    courses = Course.objects.filter(is_active=True)
    academic_years = Class.objects.values_list('academic_year', flat=True).distinct().order_by('-academic_year')
    
    # Unassigned classes
    unassigned_classes = classes.filter(instructor__isnull=True)
    
    # Classes by instructor (only assigned ones)
    instructor_classes = {}
    for instructor in instructors:
        assigned = classes.filter(instructor=instructor)
        if assigned.exists():
            instructor_classes[instructor] = assigned
    
    context = {
        'instructors': instructors,
        'courses': courses,
        'academic_years': academic_years,
        'instructor_classes': instructor_classes,
        'unassigned_classes': unassigned_classes,
        'total_classes': classes.count(),
        'assigned_count': classes.filter(instructor__isnull=False).count(),
        'unassigned_count': unassigned_classes.count(),
    }
    return render(request, 'courses/manage_instructor_assignments.html', context)


@login_required
@staff_member_required
def bulk_assign_instructors(request):
    """
    Bulk assign instructors to multiple classes
    """
    if request.method == 'POST':
        instructor_id = request.POST.get('instructor')
        class_ids = request.POST.getlist('class_ids')
        
        if instructor_id and class_ids:
            instructor = get_object_or_404(User, id=instructor_id, user_type='instructor')
            updated = Class.objects.filter(id__in=class_ids).update(instructor=instructor)
            messages.success(request, f'Successfully assigned {instructor.get_full_name()} to {updated} classes')
        else:
            messages.warning(request, 'Please select both an instructor and at least one class')
        
        return redirect('courses:manage_instructor_assignments')
    
    return redirect('courses:manage_instructor_assignments')


@login_required
@staff_member_required
def assign_instructor_to_class(request, class_id):
    """
    Assign or change instructor for a specific class
    """
    class_obj = get_object_or_404(Class, id=class_id)
    
    if request.method == 'POST':
        instructor_id = request.POST.get('instructor')
        if instructor_id:
            instructor = get_object_or_404(User, id=instructor_id, user_type='instructor')
            class_obj.instructor = instructor
            class_obj.save()
            messages.success(request, f'Instructor {instructor.get_full_name()} assigned to {class_obj.class_code}')
        else:
            class_obj.instructor = None
            class_obj.save()
            messages.success(request, f'Instructor removed from {class_obj.class_code}')
        
        return redirect('courses:manage_instructor_assignments')
    
    # GET request - show assignment form (if accessed directly)
    return redirect('courses:manage_instructor_assignments')


@login_required
@staff_member_required
def api_unassigned_classes_count(request):
    """API endpoint to get count of unassigned classes"""
    count = Class.objects.filter(
        Q(instructor__isnull=True) | Q(instructor=''),
        is_active=True
    ).count()
    return JsonResponse({'count': count})


@login_required
@staff_member_required
def api_instructors_list(request):
    """API endpoint to get list of instructors"""
    instructors = User.objects.filter(
        user_type='instructor',
        is_active=True
    ).order_by('first_name', 'last_name')
    
    data = {
        'instructors': [{
            'id': inst.id,
            'name': inst.get_full_name() or inst.username,
            'email': inst.email
        } for inst in instructors]
    }
    return JsonResponse(data)


@login_required
@staff_member_required
def api_unassigned_classes(request):
    """API endpoint to get list of unassigned classes"""
    classes = Class.objects.filter(
        Q(instructor__isnull=True) | Q(instructor=''),
        is_active=True
    ).select_related('course').order_by('class_code')
    
    data = {
        'classes': [{
            'id': cls.id,
            'class_code': cls.class_code,
            'name': cls.name,
            'course_name': cls.course.name,
            'academic_year': cls.academic_year,
            'semester': cls.semester,
            'venue': cls.venue,
            'max_students': cls.max_students
        } for cls in classes]
    }
    return JsonResponse(data)