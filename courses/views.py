from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse

from .models import Course, Class
from .forms import CourseForm, ClassForm, ClassEnrollmentForm
from students.models import Enrollment, Student

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
    """View classes taught by the instructor"""
    if request.user.user_type != 'instructor':
        messages.error(request, "This page is for instructors only.")
        return redirect('dashboard')
    
    classes = Class.objects.filter(instructor=request.user, is_active=True)
    
    # Get current and upcoming classes
    from django.utils import timezone
    today = timezone.now().date()
    
    current_classes = classes.filter(end_date__gte=today).order_by('start_date')
    past_classes = classes.filter(end_date__lt=today).order_by('-end_date')
    
    context = {
        'current_classes': current_classes,
        'past_classes': past_classes,
    }
    return render(request, 'courses/instructor_classes.html', context)

@login_required
def student_classes(request):
    """View classes enrolled by the student"""
    if request.user.user_type != 'student':
        messages.error(request, "This page is for students only.")
        return redirect('dashboard')
    
    try:
        student = request.user.student
        enrollments = Enrollment.objects.filter(
            student=student,
            is_active=True
        ).select_related('class_enrolled', 'class_enrolled__course', 'class_enrolled__instructor')
        
        context = {
            'student': student,
            'enrollments': enrollments,
        }
        return render(request, 'courses/student_classes.html', context)
        
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('dashboard')