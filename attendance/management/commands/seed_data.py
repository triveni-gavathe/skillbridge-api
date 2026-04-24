from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, date, time
from users.models import User
from attendance.models import Institution, Batch, BatchTrainer, BatchStudent, Session, Attendance


class Command(BaseCommand):
    help = 'Seeds the database with test data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding...')

        # Institutions
        inst1 = Institution.objects.create(name='Alpha Institute')
        inst2 = Institution.objects.create(name='Beta Institute')

        # Create users — one of each role
        mo = User.objects.create_user('monitor@test.com', 'Monitor One', 'pass1234', 'monitoring_officer')
        pm = User.objects.create_user('pm@test.com', 'Programme Manager', 'pass1234', 'programme_manager')
        admin1 = User.objects.create_user('admin1@test.com', 'Admin Alpha', 'pass1234', 'institution', inst1)
        admin2 = User.objects.create_user('admin2@test.com', 'Admin Beta',  'pass1234', 'institution', inst2)

        trainers = []
        for i in range(1, 5):
            inst = inst1 if i <= 2 else inst2
            t = User.objects.create_user(f'trainer{i}@test.com', f'Trainer {i}', 'pass1234', 'trainer', inst)
            trainers.append(t)

        students = []
        for i in range(1, 16):
            s = User.objects.create_user(f'student{i}@test.com', f'Student {i}', 'pass1234', 'student')
            students.append(s)

        # Batches
        b1 = Batch.objects.create(name='Web Dev Batch A', institution=inst1)
        b2 = Batch.objects.create(name='Data Science Batch B', institution=inst1)
        b3 = Batch.objects.create(name='AI Batch C', institution=inst2)

        BatchTrainer.objects.create(batch=b1, trainer=trainers[0])
        BatchTrainer.objects.create(batch=b1, trainer=trainers[1])
        BatchTrainer.objects.create(batch=b2, trainer=trainers[1])
        BatchTrainer.objects.create(batch=b3, trainer=trainers[2])
        BatchTrainer.objects.create(batch=b3, trainer=trainers[3])

        for i, student in enumerate(students):
            if i < 6:
                BatchStudent.objects.create(batch=b1, student=student)
            elif i < 11:
                BatchStudent.objects.create(batch=b2, student=student)
            else:
                BatchStudent.objects.create(batch=b3, student=student)

        # Sessions (8 total)
        sessions_data = [
            ('Intro to HTML', b1, trainers[0], date(2024, 1, 10)),
            ('CSS Basics',    b1, trainers[0], date(2024, 1, 12)),
            ('Python Basics', b2, trainers[1], date(2024, 1, 11)),
            ('Pandas 101',    b2, trainers[1], date(2024, 1, 13)),
            ('AI Overview',   b3, trainers[2], date(2024, 1, 10)),
            ('ML Basics',     b3, trainers[2], date(2024, 1, 14)),
            ('Django REST',   b1, trainers[1], date(2024, 1, 15)),
            ('Neural Nets',   b3, trainers[3], date(2024, 1, 16)),
        ]

        all_sessions = []
        for title, batch, trainer, d in sessions_data:
            s = Session.objects.create(
                batch=batch, trainer=trainer, title=title, date=d,
                start_time=time(10, 0), end_time=time(12, 0),
            )
            all_sessions.append(s)

        # Attendance records
        statuses = ['present', 'present', 'present', 'absent', 'late', 'present']
        for session in all_sessions:
            enrolled = BatchStudent.objects.filter(batch=session.batch)
            for i, bs in enumerate(enrolled):
                Attendance.objects.create(
                    session=session,
                    student=bs.student,
                    status=statuses[i % len(statuses)],
                )

        self.stdout.write(self.style.SUCCESS('Done! Database seeded.'))