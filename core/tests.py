from datetime import date,timedelta
from django.test import TestCase as DjangoTestCase
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.core.management.base import CommandError
from io import BytesIO,StringIO
from django.core.files.uploadedfile import SimpleUploadedFile
from openpyxl import Workbook
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
    def test_change_request_and_version_snapshot(self):
        group,_=Group.objects.get_or_create(name='RA_MANAGER'); self.u.groups.add(group); self.client.force_login(self.u)
        change=ChangeRequest.objects.create(project=self.p,code='',title='라벨 변경',reason='규격 변경',requester=self.u)
        self.assertEqual(change.code,'CR-001')
        response=self.client.post(f'/items/changes/{change.pk}/edit/',{'code':change.code,'title':'라벨 변경 완료','reason':'규격 변경','impact':'문서','status':'검토 중','requester':self.u.pk})
        self.assertEqual(response.status_code,302)
        self.assertEqual(VersionSnapshot.objects.filter(object_id=change.pk,model_name='ChangeRequest').count(),1)
    def test_search_title_and_project_api_filter(self):
        Requirement.objects.create(project=self.p,code='',title='배터리 안전',description='과충전 방지')
        other=Project.objects.create(code='P2',name='Other',device_name='Other')
        Requirement.objects.create(project=other,code='',title='다른 요구',description='x')
        self.client.force_login(self.u)
        self.assertContains(self.client.get(f'/items/requirements/?project={self.p.pk}&q=배터리'),'배터리 안전')
        data=self.client.get(f'/api/requirements/?project={self.p.pk}').json()
        self.assertEqual(data['count'],1)
    def test_requirement_excel_import(self):
        group,_=Group.objects.get_or_create(name='RA_MANAGER'); self.u.groups.add(group); self.client.force_login(self.u)
        wb=Workbook(); ws=wb.active; ws.append(['title','description','priority']); ws.append(['멸균 요구','멸균 조건 정의','상'])
        output=BytesIO(); wb.save(output)
        upload=SimpleUploadedFile('requirements.xlsx',output.getvalue(),content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response=self.client.post('/requirements/import/',{'project':self.p.pk,'file':upload})
        self.assertEqual(response.status_code,302)
        self.assertTrue(Requirement.objects.filter(project=self.p,title='멸균 요구',priority='상').exists())
    def test_admin_user_management_and_role_display(self):
        admin=User.objects.create_superuser('boss',password='StrongPass!1')
        self.client.force_login(admin)
        response=self.client.post('/users/',{'username':'reader','email':'reader@example.com','role':'VIEWER','password':'ReaderPass!1','is_active':'on'})
        self.assertEqual(response.status_code,302)
        reader=User.objects.get(username='reader')
        self.assertTrue(reader.groups.filter(name='VIEWER').exists())
        Requirement.objects.create(project=self.p,code='',title='조회 항목',description='')
        self.client.force_login(reader)
        page=self.client.get('/items/requirements/')
        self.assertContains(page,'일반 사용자')
        self.assertContains(page,'조회 전용')
        self.assertNotContains(page,'새 항목')
        self.assertEqual(self.client.get('/users/').status_code,403)
    def test_admin_cannot_remove_own_admin_access(self):
        admin=User.objects.create_superuser('boss2',password='StrongPass!1')
        self.client.force_login(admin)
        response=self.client.post(f'/users/{admin.pk}/',{'username':'boss2','email':'','role':'VIEWER','password':'','is_active':'on'})
        self.assertEqual(response.status_code,200)
        admin.refresh_from_db()
        self.assertTrue(admin.is_superuser and admin.is_active)
    def test_change_approval_signature_and_lock(self):
        group,_=Group.objects.get_or_create(name='RA_MANAGER'); self.u.groups.add(group); self.client.force_login(self.u)
        change=ChangeRequest.objects.create(project=self.p,code='',title='승인 대상',reason='변경 필요',status='검토 중',requester=self.u)
        bad=self.client.post(f'/items/changes/{change.pk}/approve/',{'password':'wrong','comment':'검토 완료','confirm':'on'})
        self.assertEqual(bad.status_code,200)
        self.assertFalse(ApprovalSignature.objects.filter(change_request=change).exists())
        approved=self.client.post(f'/items/changes/{change.pk}/approve/',{'password':'pw','comment':'검토 완료','confirm':'on'})
        self.assertEqual(approved.status_code,302)
        change.refresh_from_db()
        self.assertEqual(change.status,'승인')
        self.assertEqual(change.approval_signature.signer,self.u)
        self.assertEqual(len(change.approval_signature.content_hash),64)
        self.assertEqual(self.client.get(f'/items/changes/{change.pk}/edit/').status_code,409)
        self.assertEqual(self.client.post(f'/items/changes/{change.pk}/delete/').status_code,409)
    def test_audit_log_records_safe_request_details(self):
        self.client.force_login(self.u)
        self.client.post('/login/', {'username':'tester','password':'pw','note':'확인'})
        log=AuditLog.objects.latest('created_at')
        self.assertEqual(log.response_status,302)
        self.assertEqual(log.details['password'],'[REDACTED]')
        self.assertEqual(log.details['note'],'확인')
    def test_change_audit_diff_and_approval_revoke_history(self):
        group,_=Group.objects.get_or_create(name='RA_MANAGER'); self.u.groups.add(group); self.client.force_login(self.u)
        change=ChangeRequest.objects.create(project=self.p,code='',title='변경 전',reason='사유',status='검토 중',requester=self.u)
        response=self.client.post(f'/items/changes/{change.pk}/edit/',{'code':change.code,'title':'변경 후','reason':'사유','impact':'','status':'검토 중','requester':self.u.pk,'assignee':''})
        self.assertEqual(response.status_code,302)
        detail=AuditLog.objects.filter(action='수정').latest('created_at').details
        self.assertEqual(detail['changes']['title'],{'before':'변경 전','after':'변경 후'})
        self.client.post(f'/items/changes/{change.pk}/approve/',{'password':'pw','comment':'승인','confirm':'on'})
        revoked=self.client.post(f'/items/changes/{change.pk}/revoke/',{'password':'pw','reason':'내용 보완','confirm':'on'})
        self.assertEqual(revoked.status_code,302)
        change.refresh_from_db()
        self.assertEqual(change.status,'검토 중')
        self.assertFalse(hasattr(change,'approval_signature'))
        self.assertEqual(list(change.approval_events.values_list('event',flat=True)),['revoked','approved'])
        history=self.client.get(f'/items/changes/{change.pk}/history/')
        self.assertContains(history,'승인 취소')
        self.assertContains(history,'내용 보완')
    def test_audit_filter_and_csv_export(self):
        admin=User.objects.create_superuser('auditadmin',password='StrongPass!1')
        AuditLog.objects.create(user=admin,action='수정',path='/items/changes/1/edit/',method='POST',response_status=302,details={'changes':{'title':{'before':'전','after':'후'}}})
        AuditLog.objects.create(user=self.u,action='생성',path='/items/requirements/new/',method='POST',response_status=302)
        self.client.force_login(admin)
        page=self.client.get('/audit/?user=auditadmin&action=수정')
        self.assertContains(page,'변경 전·후')
        self.assertNotContains(page,'/items/requirements/new/')
        exported=self.client.get('/audit/?user=auditadmin&export=csv')
        self.assertEqual(exported.status_code,200)
        self.assertEqual(exported['Content-Type'],'text/csv; charset=utf-8')
        self.assertIn('audit-log.csv',exported['Content-Disposition'])
