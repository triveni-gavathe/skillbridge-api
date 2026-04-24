"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from users.views import (
    SignupView, LoginView, MonitoringTokenView,
    MeView, ChangePasswordView, UserListView
)
from attendance.views import (
    BatchCreateView, BatchInviteView, BatchJoinView,
    SessionCreateView, AttendanceMarkView, SessionAttendanceView,
    BatchSummaryView, InstitutionSummaryView,
    ProgrammeSummaryView, MonitoringAttendanceView,
)

urlpatterns = [
    # Auth
    path('auth/signup', SignupView.as_view()),
    path('auth/login', LoginView.as_view()),
    path('auth/monitoring-token', MonitoringTokenView.as_view()),
    path('auth/me', MeView.as_view()),
    path('auth/change-password', ChangePasswordView.as_view()),

    # Users
    path('users', UserListView.as_view()),

    # Batches
    path('batches', BatchCreateView.as_view()),
    path('batches/<int:pk>/invite', BatchInviteView.as_view()),
    path('batches/join', BatchJoinView.as_view()),
    path('batches/<int:pk>/summary', BatchSummaryView.as_view()),

    # Sessions
    path('sessions', SessionCreateView.as_view()),
    path('sessions/<int:pk>/attendance', SessionAttendanceView.as_view()),

    # Attendance
    path('attendance/mark', AttendanceMarkView.as_view()),

    # Summaries
    path('institutions/<int:pk>/summary', InstitutionSummaryView.as_view()),
    path('programme/summary', ProgrammeSummaryView.as_view()),

    # Monitoring
    path('monitoring/attendance', MonitoringAttendanceView.as_view()),
]