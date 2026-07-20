from django.contrib import admin
from .models import *
for model in [Project,Requirement,DesignItem,Risk,TestCase,TestResult,Incident,CAPA,AuditLog]: admin.site.register(model)

