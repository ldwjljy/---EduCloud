
import os
import django
import random
from datetime import timedelta
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EduCloud.settings')
django.setup()

from accounts.models import StudentProfile
from courses.models import CourseSchedule
from attendance_app.models import Attendance

def populate_attendance():
    print("Populating attendance data...")
    students = list(StudentProfile.objects.all())
    schedules = list(CourseSchedule.objects.all())
    
    if not students or not schedules:
        print("No students or schedules found. Skipping.")
        return

    now = timezone.now().date()
    # Generate for last 7 days
    for i in range(7):
        date = now - timedelta(days=i)
        print(f"Generating for {date}...")
        
        # For each day, pick random schedules and students
        # Simulate 100 records per day
        for _ in range(50):
            student = random.choice(students)
            schedule = random.choice(schedules)
            
            # Weighted random status
            # 80% present, 10% late, 5% absent, 5% leave
            rand = random.random()
            if rand < 0.8:
                status = 'present'
            elif rand < 0.9:
                status = 'late'
            elif rand < 0.95:
                status = 'absent'
            else:
                status = 'leave'
            
            Attendance.objects.get_or_create(
                student=student, 
                schedule=schedule, 
                date=date,
                defaults={'status': status}
            )
            
    print("Done!")

if __name__ == '__main__':
    populate_attendance()
