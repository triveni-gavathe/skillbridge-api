from django.db import models

# Create your models here.

from django.conf import settings
import uuid


class Institution(models.Model):
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Batch(models.Model):
    name = models.CharField(max_length=200)
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='batches')
    trainers = models.ManyToManyField(
        settings.AUTH_USER_MODEL, through='BatchTrainer', related_name='trainer_batches', blank=True
    )
    students = models.ManyToManyField(
        settings.AUTH_USER_MODEL, through='BatchStudent', related_name='student_batches', blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class BatchTrainer(models.Model):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)
    trainer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('batch', 'trainer')


class BatchStudent(models.Model):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('batch', 'student')


class BatchInvite(models.Model):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='invites')
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)

    def __str__(self):
        return f"Invite for {self.batch.name}"


class Session(models.Model):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='sessions')
    trainer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=300)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Attendance(models.Model):
    STATUS_CHOICES = [('present', 'Present'), ('absent', 'Absent'), ('late', 'Late')]

    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='attendances')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    marked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('session', 'student')

    def __str__(self):
        return f"{self.student.email} - {self.session.title} - {self.status}"