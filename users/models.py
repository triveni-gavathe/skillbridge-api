from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, name, password, role, institution=None):
        if not email:
            raise ValueError('Email required')
        user = self.model(
            email=self.normalize_email(email),
            name=name,
            role=role,
            institution=institution,
        )
        user.set_password(password)   # hashes with bcrypt via Django
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password, role='student'):
        user = self.create_user(email, name, password, role)
        user.is_admin = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    ROLES = [
        ('student', 'Student'),
        ('trainer', 'Trainer'),
        ('institution', 'Institution'),
        ('programme_manager', 'Programme Manager'),
        ('monitoring_officer', 'Monitoring Officer'),
    ]

    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=30, choices=ROLES)
    institution = models.ForeignKey(
        'attendance.Institution', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='members'
    )
    is_admin = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    def __str__(self):
        return f"{self.email} ({self.role})"

    @property
    def is_staff(self):
        return self.is_admin