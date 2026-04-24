from rest_framework.generics import (
    CreateAPIView, RetrieveAPIView, ListAPIView
)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta

from attendance.models import (
    Batch, BatchTrainer, BatchStudent,
    BatchInvite, Session, Attendance, Institution
)
from attendance.serializers import (
    BatchSerializer, SessionSerializer,
    AttendanceSerializer, BatchInviteSerializer
)
from users.permissions import (
    IsTrainer, IsStudent, IsInstitution,
    IsTrainerOrInstitution, IsProgrammeManager, IsMonitoringOfficer
)


# POST /batches — Trainer or Institution
class BatchCreateView(CreateAPIView):
    serializer_class = BatchSerializer
    permission_classes = [IsTrainerOrInstitution]

    def perform_create(self, serializer):
        batch = serializer.save()
        # auto-assign trainer to their own batch
        if self.request.user.role == 'trainer':
            BatchTrainer.objects.create(batch=batch, trainer=self.request.user)


# POST /batches/{id}/invite — Trainer only
class BatchInviteView(APIView):
    permission_classes = [IsTrainer]

    def post(self, request, pk):
        batch = get_object_or_404(Batch, pk=pk)
        invite = BatchInvite.objects.create(
            batch=batch,
            created_by=request.user,
            expires_at=timezone.now() + timedelta(days=7),
        )
        serializer = BatchInviteSerializer(invite)
        return Response(serializer.data, status=201)


# POST /batches/join — Student only
class BatchJoinView(APIView):
    permission_classes = [IsStudent]

    def post(self, request):
        token = request.data.get('token')
        if not token:
            return Response({'error': 'token is required.'}, status=422)

        invite = get_object_or_404(BatchInvite, token=token)

        if invite.used:
            return Response({'error': 'Invite already used.'}, status=400)
        if invite.expires_at < timezone.now():
            return Response({'error': 'Invite has expired.'}, status=400)

        BatchStudent.objects.get_or_create(batch=invite.batch, student=request.user)
        invite.used = True
        invite.save()
        return Response({'message': f'Joined batch: {invite.batch.name}'})


# POST /sessions — Trainer only
class SessionCreateView(CreateAPIView):
    serializer_class = SessionSerializer
    permission_classes = [IsTrainer]

    def perform_create(self, serializer):
        serializer.save(trainer=self.request.user)


# POST /attendance/mark — Student only
class AttendanceMarkView(APIView):
    permission_classes = [IsStudent]

    def post(self, request):
        # Accept both 'session_id' and 'session' field names
        session_id = request.data.get('session_id') or request.data.get('session')
        status_val = request.data.get('status')

        # Manual validation — return 422 with clear errors
        errors = {}
        if not session_id:
            errors['session_id'] = 'This field is required.'
        if not status_val:
            errors['status'] = 'This field is required.'
        elif status_val not in ['present', 'absent', 'late']:
            errors['status'] = 'Must be one of: present, absent, late.'
        if errors:
            return Response(errors, status=422)

        session = get_object_or_404(Session, pk=session_id)

        # Student must be enrolled in this session's batch
        enrolled = BatchStudent.objects.filter(
            batch=session.batch, student=request.user
        ).exists()
        if not enrolled:
            return Response(
                {'error': 'You are not enrolled in this session.'},
                status=403
            )

        attendance, created = Attendance.objects.get_or_create(
            session=session,
            student=request.user,
            defaults={'status': status_val},
        )
        if not created:
            attendance.status = status_val
            attendance.save()

        return Response({
            'id': attendance.id,
            'session': session.id,
            'student': request.user.id,
            'status': attendance.status,
            'marked_at': attendance.marked_at,
        })
# GET /sessions/{id}/attendance — Trainer only
class SessionAttendanceView(ListAPIView):
    serializer_class = AttendanceSerializer
    permission_classes = [IsTrainer]

    def get_queryset(self):
        session = get_object_or_404(Session, pk=self.kwargs['pk'])
        return Attendance.objects.filter(session=session).select_related('student')


# GET /batches/{id}/summary — Institution only
class BatchSummaryView(APIView):
    permission_classes = [IsInstitution]

    def get(self, request, pk):
        batch = get_object_or_404(Batch, pk=pk)
        sessions = Session.objects.filter(batch=batch)
        total = Attendance.objects.filter(session__in=sessions).count()
        present = Attendance.objects.filter(session__in=sessions, status='present').count()
        return Response({
            'batch': batch.name,
            'total_sessions': sessions.count(),
            'total_records': total,
            'present': present,
            'absent': total - present,
        })


# GET /institutions/{id}/summary — Programme Manager only
class InstitutionSummaryView(APIView):
    permission_classes = [IsProgrammeManager]

    def get(self, request, pk):
        institution = get_object_or_404(Institution, pk=pk)
        batches = Batch.objects.filter(institution=institution)
        data = []
        for batch in batches:
            sessions = Session.objects.filter(batch=batch)
            total = Attendance.objects.filter(session__in=sessions).count()
            present = Attendance.objects.filter(session__in=sessions, status='present').count()
            data.append({'batch': batch.name, 'total': total, 'present': present})
        return Response({'institution': institution.name, 'batches': data})


# GET /programme/summary — Programme Manager only
class ProgrammeSummaryView(ListAPIView):
    permission_classes = [IsProgrammeManager]

    def list(self, request):
        data = []
        for inst in Institution.objects.all():
            batches = Batch.objects.filter(institution=inst)
            sessions = Session.objects.filter(batch__in=batches)
            total = Attendance.objects.filter(session__in=sessions).count()
            present = Attendance.objects.filter(session__in=sessions, status='present').count()
            data.append({'institution': inst.name, 'total': total, 'present': present})
        return Response(data)


# GET /monitoring/attendance — Monitoring Officer only (scoped token)
class MonitoringAttendanceView(ListAPIView):
    serializer_class = AttendanceSerializer
    permission_classes = [IsMonitoringOfficer]

    def get_queryset(self):
        return Attendance.objects.select_related('student', 'session').all()

    def post(self, request):   return Response(status=405)
    def put(self, request):    return Response(status=405)
    def patch(self, request):  return Response(status=405)
    def delete(self, request): return Response(status=405)