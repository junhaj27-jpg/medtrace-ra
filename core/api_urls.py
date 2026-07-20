from django.urls import include,path
from rest_framework.routers import DefaultRouter
from .api import *
r=DefaultRouter(); r.register('projects',ProjectViewSet); r.register('requirements',RequirementViewSet); r.register('risks',RiskViewSet); r.register('tests',TestViewSet); r.register('incidents',IncidentViewSet); r.register('capa',CAPAViewSet)
urlpatterns=[path('auth/login/',login_api),path('auth/logout/',logout_api),path('admin/users/',admin_users_api),path('traceability/',trace_api),path('traceability/gaps/',gaps_api),path('dashboard/summary/',summary_api),path('',include(r.urls))]
