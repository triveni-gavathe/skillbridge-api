import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from users.models import User
from attendance.models import Institution, Batch, BatchStudent, Session
from users.authentication import generate_token
from datetime import date, time

ATOMIC_REQUESTS = False
@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def institution(db):
    return Institution.objects.create(name='Test Institute')


@pytest.fixture
def student(db):
    return User.objects.create_user('stu@test.com', 'Student One', 'pass1234', 'student')


@pytest.fixture
def trainer(db):
    return User.objects.create_user('trainer@test.com', 'Trainer One', 'pass1234', 'trainer')


@pytest.fixture
def batch(db, institution, trainer):
    b = Batch.objects.create(name='Test Batch', institution=institution)
    from attendance.models import BatchTrainer
    BatchTrainer.objects.create(batch=b, trainer=trainer)
    return b


@pytest.fixture
def session(db, batch, trainer):
    return Session.objects.create(
        batch=batch, trainer=trainer, title='Test Session',
        date=date(2024, 1, 10), start_time=time(9, 0), end_time=time(11, 0),
    )


# Test 1: Signup and login return valid JWT
@pytest.mark.django_db
def test_signup_and_login(client):
    res = client.post('/auth/signup', {
        'name': 'New User', 'email': 'new@test.com',
        'password': 'pass1234', 'role': 'student',
    }, format='json')
    assert res.status_code == 201
    assert 'token' in res.data

    res2 = client.post('/auth/login', {
        'email': 'new@test.com', 'password': 'pass1234',
    }, format='json')
    assert res2.status_code == 200
    assert 'token' in res2.data


# Test 2: Trainer can create a session
@pytest.mark.django_db
def test_trainer_creates_session(client, trainer, batch):
    token = generate_token(trainer)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    res = client.post('/sessions', {
        'batch': batch.id, 'title': 'New Session',
        'date': '2024-02-01', 'start_time': '10:00', 'end_time': '12:00',
    }, format='json')
    assert res.status_code == 201
    assert res.data['title'] == 'New Session'


# Test 3: Student marks their own attendance
@pytest.mark.django_db
def test_student_marks_attendance(client, student, batch, session):
    BatchStudent.objects.create(batch=batch, student=student)
    token = generate_token(student)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    res = client.post('/attendance/mark', {
        'session_id': session.id, 'status': 'present',
    }, format='json')
    print(res.data)
    assert res.status_code == 200
    assert res.data['status'] == 'present'


# Test 4: POST to /monitoring/attendance returns 405
@pytest.mark.django_db
def test_monitoring_post_returns_405(client):
    mo = User.objects.create_user('mo@test.com', 'Monitor', 'pass1234', 'monitoring_officer')
    token = generate_token(mo, token_type='monitoring')
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    res = client.post('/monitoring/attendance', {}, format='json')
    assert res.status_code == 405


# Test 5: Protected endpoint without token returns 401
@pytest.mark.django_db
def test_no_token_returns_401(client):
    res = client.get('/monitoring/attendance')
    assert res.status_code in [401, 403]