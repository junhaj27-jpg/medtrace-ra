from datetime import date,timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User,Group
from core.models import *
class Command(BaseCommand):
    help='가상의 이동강도 모니터 프로젝트와 역할별 계정을 생성합니다.'
    def handle(self,*a,**k):
        for name in ['ADMIN','RA_MANAGER','DEVELOPER','TESTER','VIEWER']: Group.objects.get_or_create(name=name)
        admin,_=User.objects.get_or_create(username='admin',defaults={'is_staff':True,'is_superuser':True,'email':'admin@example.invalid'}); admin.set_password('MedTrace!2026'); admin.save()
        for username,group in [('ra_manager','RA_MANAGER'),('developer','DEVELOPER'),('tester','TESTER'),('viewer','VIEWER')]:
            u,_=User.objects.get_or_create(username=username); u.set_password('Demo!2026'); u.save(); u.groups.add(Group.objects.get(name=group))
        p,_=Project.objects.get_or_create(code='MTR-001',defaults={'name':'웨어러블 심박수 기반 이동강도 모니터','device_name':'MovePulse Demo','device_class':'교육용 분류','model_name':'MP-100','manager':admin,'start_date':date.today()-timedelta(days=90),'target_date':date.today()+timedelta(days=90),'description':'모든 데이터는 가상입니다.'})
        data=[('사용자의 심박수를 측정해야 한다.','기능 요구사항'),('목표 심박수 도달 시 알림을 제공해야 한다.','기능 요구사항'),('비정상 센서 데이터는 화면에 경고해야 한다.','안전 요구사항'),('이동 세션 기록을 저장해야 한다.','시스템 요구사항'),('사용자 데이터 접근을 권한별로 제한해야 한다.','보안 요구사항')]
        req=[]
        for title,typ in data:
            x,_=Requirement.objects.get_or_create(project=p,title=title,defaults={'code':'','description':title,'req_type':typ,'status':'승인','created_by':admin}); req.append(x)
        d,_=DesignItem.objects.get_or_create(project=p,title='센서 수집 및 검증 모듈',defaults={'code':'','description':'센서 범위 검사와 상태 표시','created_by':admin}); d.requirements.add(*req[:3])
        risk,_=Risk.objects.get_or_create(project=p,hazard='센서 오류로 잘못된 심박수 표시',defaults={'code':'','harm':'잘못된 운동 판단','probability':3,'severity':4,'control':'범위 검증 및 연속 비정상값 필터','residual_probability':1,'residual_severity':4,'residual_acceptable':True,'created_by':admin}); risk.requirements.add(req[0],req[2]); risk.designs.add(d)
        for i,r in enumerate(req):
            t,_=TestCase.objects.get_or_create(project=p,name=f'{r.title} 검증',defaults={'code':'','purpose':'요구사항 검증','procedure':'정상값과 경계값을 입력하고 동작을 관찰한다.','expected':'정의된 동작과 일치한다.','created_by':admin}); t.requirements.add(r)
            if i<4: TestResult.objects.get_or_create(test_case=t,defaults={'actual':'예상 동작 확인','outcome':'PASS','tested_at':date.today(),'tester':admin,'created_by':admin})
        inc,_=Incident.objects.get_or_create(project=p,title='센서 접촉 불량 시 일시적 고 BPM 표시',defaults={'code':'','occurred_at':date.today()-timedelta(days=10),'description':'시험 중 관찰된 가상 사례','severity':3,'related_test':p.tests.first(),'created_by':admin})
        CAPA.objects.get_or_create(project=p,title='센서 값 연속성 필터 개선',defaults={'code':'','cause':'접촉 상태 판별 부족','corrective_action':'연속 비정상값 필터 추가','preventive_action':'연결 상태 표시 개선','target_date':date.today()+timedelta(days=30),'status':'진행 중','incident':inc,'risk':risk,'created_by':admin})
        self.stdout.write(self.style.SUCCESS('데모 데이터 생성 완료: admin / MedTrace!2026'))

