from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
import csv
from io import TextIOWrapper

from .models import Student, Enrollment, AcademicRecord
from .forms import StudentRegistrationForm, StudentUpdateForm, EnrollmentForm, BulkStudentImportForm
from accounts.models import User

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