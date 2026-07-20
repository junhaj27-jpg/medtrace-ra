from .models import Requirement,Risk,TestCase,CAPA
def project_summary(project):
    reqs=project.requirements.all(); approved=reqs.filter(status='승인'); linked=approved.filter(tests__isnull=False).distinct().count()
    tests=project.tests.all(); results=[getattr(x,'result',None) for x in tests]
    return {'requirements':reqs.count(),'approved':approved.count(),'unlinked':approved.filter(tests__isnull=True).count(),'risks':project.risks.count(),'high_risks':sum(r.score>=10 for r in project.risks.all()),'tests':tests.count(),'passed':sum(bool(r) and r.outcome=='PASS' for r in results),'failed':sum(bool(r) and r.outcome=='FAIL' for r in results),'coverage':round(linked/approved.count()*100,1) if approved.count() else 0,'open_capa':project.capas.exclude(status__in=['완료','취소']).count(),'overdue_capa':sum(c.overdue for c in project.capas.all()),'incidents':project.incidents.exclude(investigation_status='종결').count()}
def trace_rows(project):
    rows=[]
    for req in project.requirements.prefetch_related('designs','risks','tests__capas'):
        tests=list(req.tests.all()); risks=list(req.risks.all()); designs=list(req.designs.all()); capas=[]
        for t in tests: capas.extend(t.capas.all())
        gap=[]
        if req.status=='승인' and not tests: gap.append('시험 미연결')
        if not risks: gap.append('위험 미연결')
        if tests and any(not hasattr(t,'result') for t in tests): gap.append('결과 미등록')
        if any(hasattr(t,'result') and t.result.outcome=='FAIL' and not t.capas.exists() for t in tests): gap.append('FAIL 조치 미연결')
        rows.append({'req':req,'designs':designs,'risks':risks,'tests':tests,'capas':capas,'status':'완료' if not gap else ' · '.join(gap)})
    return rows
