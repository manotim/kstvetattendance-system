#!/usr/bin/env python
"""
Quick database check
"""

import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tvet_attendance.settings')
django.setup()

from django.db import connection
from django.contrib.auth import get_user_model

User = get_user_model()

# Check all tables
with connection.cursor() as cursor:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print("📊 DATABASE TABLES:")
    print("=" * 50)
    for table in tables:
        table_name = table[0]
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"{table_name:30} | {count:5} records")

print("\n" + "=" * 50)
print("Checking specific models:")

# Check specific models
try:
    from courses.models import Course, Class
    from students.models import Student
    from attendance.models import AttendanceSession
    
    print(f"\n📚 Courses: {Course.objects.count()}")
    print(f"🏫 Classes: {Class.objects.count()}")
    print(f"👨‍🎓 Students: {Student.objects.count()}")
    print(f"✅ Attendance Sessions: {AttendanceSession.objects.count()}")
except Exception as e:
    print(f"\n⚠️ Error checking models: {e}")