from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Seed accounts data'

    def handle(self, *args, **kwargs):
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
            self.stdout.write(self.style.SUCCESS(f'Created admin: {admin.username}'))
        
        # Create instructor
        instructor, created = User.objects.get_or_create(
            username='instructor1',
            defaults={
                'email': 'instructor@tvet.ac.ke',
                'first_name': 'John',
                'last_name': 'Kamau',
                'user_type': 'instructor',
                'department': 'Computer Science',
            }
        )
        if created:
            instructor.set_password('instructor123')
            instructor.save()
            self.stdout.write(self.style.SUCCESS(f'Created instructor: {instructor.username}'))
        
        # Create student user
        student_user, created = User.objects.get_or_create(
            username='student1',
            defaults={
                'email': 'student@tvet.ac.ke',
                'first_name': 'Brian',
                'last_name': 'Mutua',
                'user_type': 'student',
            }
        )
        if created:
            student_user.set_password('student123')
            student_user.save()
            self.stdout.write(self.style.SUCCESS(f'Created student user: {student_user.username}'))
        
        self.stdout.write(self.style.SUCCESS('Accounts seeded successfully!'))