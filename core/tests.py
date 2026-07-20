from datetime import date,timedelta
from django.test import TestCase as DjangoTestCase
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.core.management.base import CommandError
from io import StringIO
from .models import *
from .services import project_summary,trace_rows
class TestMedTrace(DjangoTestCase):
    def setUp(self):
        self.u=User.objects.create_user('tester',password='pw'); self.p=Project.objects.create(code='P1',name='Demo',device_name='Device',created_by=self.u)
    def test_login_required_and_login(self):
        self.assertEqual(self.client.get('/').status_code,302); self.assertTrue(self.client.login(username='tester',password='pw')); self.assertEqual(self.client.get('/').status_code,200)
        projects=self.client.get('/projects/'); self.assertContains(projects,'Demo'); self.assertNotContains(projects,'/items/projects/')
    def test_auto_ids(self):
        r=Requirement.objects.create(project=self.p,code='',title='R',description='D'); self.assertEqual(r.code,'REQ-001')
        r2=Requirement.objects.create(project=self.p,code='',title='R2',description='D'); self.assertEqual(r2.code,'REQ-002')
    def test_risk_scores(self):
        r=Risk.objects.create(project=self.p,code='',hazard='H',probability=4,severity=4,residual_probability=1,residual_severity=4)
        self.assertEqual(r.score,16); self.assertEqual(r.residual_score,4); self.assertEqual(r.level,'높음')
    def test_coverage_and_gap(self):
        r=Requirement.objects.create(project=self.p,code='',title='R',description='D',status='승인'); self.assertIn('시험 미연결',trace_rows(self.p)[0]['status'])
        t=TestCase.objects.create(project=self.p,code='',name='T',procedure='P',expected='E'); t.requirements.add(r)
        self.assertEqual(project_summary(self.p)['coverage'],100)
    def test_fail_without_capa_gap(self):
        r=Requirement.objects.create(project=self.p,code='',title='R',description='D',status='승인'); t=TestCase.objects.create(project=self.p,code='',name='T',procedure='P',expected='E'); t.requirements.add(r); TestResult.objects.create(test_case=t,actual='x',outcome='FAIL',tested_at=date.today())
        self.assertIn('FAIL 조치 미연결',trace_rows(self.p)[0]['status'])
    def test_capa_overdue(self):
        c=CAPA.objects.create(project=self.p,code='',title='C',cause='x',corrective_action='x',target_date=date.today()-timedelta(days=1)); self.assertTrue(c.overdue)
    def test_exports(self):
        self.client.force_login(self.u)
        for fmt in ['xlsx','docx','pdf']:
            res=self.client.get(f'/export/{fmt}/?project={self.p.pk}'); self.assertEqual(res.status_code,200); self.assertGreater(len(res.content),100)
    def test_api_auth_and_project(self):
        self.assertEqual(self.client.get('/api/projects/').status_code,403); self.client.force_login(self.u); self.assertEqual(self.client.get('/api/projects/').status_code,200)
    def test_all_normalized_list_pages_render_for_viewer(self):
        Requirement.objects.create(project=self.p,code='',title='요구 제목',description='')
        Risk.objects.create(project=self.p,code='',hazard='센서 위험',probability=2,severity=3)
        TestCase.objects.create(project=self.p,code='',name='시험 이름',procedure='P',expected='E')
        Incident.objects.create(project=self.p,code='',title='가상 사례',occurred_at=date.today(),description='',investigation_status='조사 중')
        CAPA.objects.create(project=self.p,code='',title='조치 제목',cause='',corrective_action='',target_date=date.today())
        self.client.force_login(self.u)
        expected={'/requirements/':'요구 제목','/risks/':'센서 위험','/tests/':'시험 이름','/incidents/':'조사 중','/capa/':'조치 제목'}
        for url,text in expected.items():
            response=self.client.get(url); self.assertEqual(response.status_code,200,url); self.assertContains(response,text)
    def test_create_and_promote_admin_commands(self):
        call_command('create_admin',username='newadmin',email='admin@example.com',password='SafePass!2026',stdout=StringIO())
        admin=User.objects.get(username='newadmin'); self.assertTrue(admin.is_superuser and admin.is_staff and admin.is_active); self.assertTrue(admin.check_password('SafePass!2026')); self.assertTrue(admin.groups.filter(name='ADMIN').exists())
        call_command('promote_admin',username='tester',stdout=StringIO()); self.u.refresh_from_db(); self.assertTrue(self.u.is_superuser); self.assertTrue(self.u.groups.filter(name='ADMIN').exists())
        with self.assertRaises(CommandError): call_command('create_admin',username='bad',password='short')
    def test_admin_group_full_access_and_viewer_restrictions(self):
        viewer=User.objects.create_user('viewer2',password='pw'); self.client.force_login(viewer)
        self.assertEqual(self.client.get('/audit/').status_code,403); self.assertEqual(self.client.get('/projects/new/').status_code,403); self.assertEqual(self.client.get('/api/admin/users/').status_code,403)
        group,_=Group.objects.get_or_create(name='ADMIN'); viewer.groups.add(group)
        self.assertEqual(self.client.get('/audit/').status_code,200); self.assertEqual(self.client.get('/projects/new/').status_code,200); self.assertEqual(self.client.get('/api/admin/users/').status_code,200)
    def test_inactive_admin_cannot_login(self):
        admin=User.objects.create_superuser('inactive',password='StrongPass!1'); admin.is_active=False; admin.save()
        self.assertFalse(self.client.login(username='inactive',password='StrongPass!1'))
