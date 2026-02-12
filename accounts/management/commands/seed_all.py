from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):
    help = 'Seed all data for TVET Attendance System'

    def handle(self, *args, **kwargs):
        self.stdout.write("🌱 TVET ATTENDANCE SYSTEM - DATA SEEDING")
        self.stdout.write("=" * 50)
        
        try:
            # Run all seeders in order
            self.stdout.write("\n1. Seeding accounts...")
            call_command('seed_accounts')
            
            self.stdout.write("\n2. Seeding courses...")
            call_command('seed_courses')
            
            self.stdout.write("\n3. Seeding students...")
            call_command('seed_students')
            
            self.stdout.write("\n4. Seeding attendance...")
            call_command('seed_attendance')
            
            self.stdout.write("\n5. Seeding reports...")
            call_command('seed_reports')
            
            self.stdout.write("\n" + "=" * 50)
            self.stdout.write(self.style.SUCCESS("✅ ALL DATA SEEDED SUCCESSFULLY!"))
            
            self.stdout.write("\n🔐 LOGIN CREDENTIALS:")
            self.stdout.write("=" * 50)
            self.stdout.write("Admin:     username='admin', password='admin123'")
            self.stdout.write("Instructor: username='instructor1', password='instructor123'")
            self.stdout.write("Student:   username='student1', password='student123'")
            self.stdout.write("           Admission No: TVET2024001")
            self.stdout.write("\n🌐 Access the system at: http://127.0.0.1:8000/")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error during seeding: {str(e)}"))