from rest_framework import serializers
from .models import Project,Requirement,Risk,TestCase,TestResult,Incident,CAPA
class ProjectSerializer(serializers.ModelSerializer):
    class Meta: model=Project; fields='__all__'
class RequirementSerializer(serializers.ModelSerializer):
    class Meta: model=Requirement; fields='__all__'; read_only_fields=('code','created_by')
class RiskSerializer(serializers.ModelSerializer):
    score=serializers.IntegerField(read_only=True); residual_score=serializers.IntegerField(read_only=True); level=serializers.CharField(read_only=True)
    class Meta: model=Risk; fields='__all__'; read_only_fields=('code','created_by')
class TestCaseSerializer(serializers.ModelSerializer):
    class Meta: model=TestCase; fields='__all__'; read_only_fields=('code','created_by')
class TestResultSerializer(serializers.ModelSerializer):
    class Meta: model=TestResult; fields='__all__'; read_only_fields=('created_by',)
class IncidentSerializer(serializers.ModelSerializer):
    class Meta: model=Incident; fields='__all__'; read_only_fields=('code','created_by')
class CAPASerializer(serializers.ModelSerializer):
    overdue=serializers.BooleanField(read_only=True)
    class Meta: model=CAPA; fields='__all__'; read_only_fields=('code','created_by')

