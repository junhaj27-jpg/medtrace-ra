from django.contrib.auth import authenticate,login,logout
from rest_framework import viewsets,status
from rest_framework.decorators import api_view,action,permission_classes
from rest_framework.response import Response
from .models import *
from .serializers import *
from .services import project_summary,trace_rows
from .permissions import IsSystemAdmin
class OwnedMixin:
    def perform_create(self,s): s.save(created_by=self.request.user)
class ProjectViewSet(OwnedMixin,viewsets.ModelViewSet): queryset=Project.objects.all(); serializer_class=ProjectSerializer
class RequirementViewSet(OwnedMixin,viewsets.ModelViewSet): queryset=Requirement.objects.all(); serializer_class=RequirementSerializer
class RiskViewSet(OwnedMixin,viewsets.ModelViewSet): queryset=Risk.objects.all(); serializer_class=RiskSerializer
class TestViewSet(OwnedMixin,viewsets.ModelViewSet):
    queryset=TestCase.objects.all(); serializer_class=TestCaseSerializer
    @action(detail=True,methods=['post'])
    def result(self,request,pk=None):
        s=TestResultSerializer(data={**request.data,'test_case':self.get_object().pk}); s.is_valid(raise_exception=True); s.save(created_by=request.user); return Response(s.data,status=201)
class IncidentViewSet(OwnedMixin,viewsets.ModelViewSet): queryset=Incident.objects.all(); serializer_class=IncidentSerializer
class CAPAViewSet(OwnedMixin,viewsets.ModelViewSet): queryset=CAPA.objects.all(); serializer_class=CAPASerializer
@api_view(['POST'])
def login_api(request):
    u=authenticate(request,username=request.data.get('username'),password=request.data.get('password'))
    if not u:return Response({'detail':'인증 정보가 올바르지 않습니다.'},status=400)
    login(request,u); return Response({'username':u.username})
@api_view(['POST'])
def logout_api(request): logout(request); return Response(status=204)
@api_view(['GET'])
def trace_api(request):
    p=Project.objects.get(pk=request.GET.get('project') or Project.objects.first().pk)
    return Response([{'requirement':r['req'].code,'designs':[x.code for x in r['designs']],'risks':[x.code for x in r['risks']],'tests':[x.code for x in r['tests']],'status':r['status']} for r in trace_rows(p)])
@api_view(['GET'])
def gaps_api(request):
    response=trace_api(request); response.data=[r for r in response.data if r['status']!='완료']; return response
@api_view(['GET'])
def summary_api(request):
    p=Project.objects.get(pk=request.GET.get('project') or Project.objects.first().pk); return Response(project_summary(p))
@api_view(['GET'])
@permission_classes([IsSystemAdmin])
def admin_users_api(request):
    return Response([{'username':u.username,'email':u.email,'active':u.is_active,'staff':u.is_staff} for u in User.objects.order_by('username')])
