from io import BytesIO
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.http import HttpResponse
from django.shortcuts import get_object_or_404,redirect,render
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import *
from .forms import *
from .services import project_summary,trace_rows
from .permissions import admin_required,has_full_access

MODEL_MAP={'requirements':(Requirement,RequirementForm,'요구사항'),'designs':(DesignItem,DesignItemForm,'설계'),'risks':(Risk,RiskForm,'위험'),'tests':(TestCase,TestCaseForm,'시험'),'incidents':(Incident,IncidentForm,'이상사례'),'capas':(CAPA,CAPAForm,'CAPA')}
def can_edit(user): return has_full_access(user) or user.groups.filter(name__in=['RA_MANAGER','DEVELOPER','TESTER']).exists()
def list_item(obj,kind):
    """서로 다른 모델을 목록 템플릿용 공통 표현으로 변환한다."""
    title=getattr(obj,'name',None) or getattr(obj,'title',None) or getattr(obj,'hazard',None) or getattr(obj,'test_name',None) or getattr(obj,'incident_summary',None) or '-'
    status=getattr(obj,'status',None) or getattr(obj,'investigation_status',None) or '-'
    code=getattr(obj,'code',None) or getattr(obj,'project_id',None) or f'ID-{obj.pk}'
    edit_url=reverse('project_edit',args=[obj.pk]) if kind=='projects' else reverse('object_edit',args=[kind,obj.pk])
    delete_url=None if kind=='projects' else reverse('object_delete',args=[kind,obj.pk])
    return {'pk':obj.pk,'code':code,'title':title,'status':status,'updated_at':getattr(obj,'updated_at',None),'edit_url':edit_url,'delete_url':delete_url,'has_result':kind=='tests'}
@login_required
def dashboard(request):
    project=Project.objects.first(); summary=project_summary(project) if project else None
    return render(request,'dashboard.html',{'project':project,'summary':summary,'projects':Project.objects.all(),'recent':AuditLog.objects.order_by('-created_at')[:8]})
@login_required
def projects(request):
    return render(request,'list.html',{'title':'프로젝트','items':[list_item(x,'projects') for x in Project.objects.all()],'kind':'projects'})
@login_required
def project_form(request,pk=None):
    if not can_edit(request.user): return HttpResponse('수정 권한이 없습니다.',status=403)
    obj=get_object_or_404(Project,pk=pk) if pk else None; form=ProjectForm(request.POST or None,instance=obj)
    if request.method=='POST' and form.is_valid():
        x=form.save(commit=False); x.created_by=x.created_by or request.user; x.save(); messages.success(request,'프로젝트가 저장되었습니다.'); return redirect('projects')
    return render(request,'form.html',{'form':form,'title':'프로젝트 저장'})
@login_required
def object_list(request,kind):
    model,form,label=MODEL_MAP[kind]; project=get_object_or_404(Project,pk=request.GET.get('project') or Project.objects.values_list('pk',flat=True).first()); qs=model.objects.filter(project=project)
    q=request.GET.get('q','');
    if q: qs=qs.filter(code__icontains=q)
    return render(request,'list.html',{'title':label,'items':[list_item(x,kind) for x in qs],'kind':kind,'project':project})
@login_required
def object_form(request,kind,pk=None):
    if not can_edit(request.user): return HttpResponse('수정 권한이 없습니다.',status=403)
    model,form_cls,label=MODEL_MAP[kind]; obj=get_object_or_404(model,pk=pk) if pk else None; project=obj.project if obj else get_object_or_404(Project,pk=request.GET.get('project') or Project.objects.values_list('pk',flat=True).first()); form=form_cls(request.POST or None,instance=obj)
    if request.method=='POST' and form.is_valid():
        x=form.save(commit=False); x.project=project; x.created_by=x.created_by or request.user; x.save(); form.save_m2m(); messages.success(request,f'{label} 항목이 저장되었습니다.'); return redirect('object_list',kind=kind)
    return render(request,'form.html',{'form':form,'title':f'{label} 저장','project':project})
@require_POST
@login_required
def object_delete(request,kind,pk):
    if not can_edit(request.user): return HttpResponse(status=403)
    MODEL_MAP[kind][0].objects.filter(pk=pk).delete(); messages.success(request,'삭제되었습니다.'); return redirect('object_list',kind=kind)
@login_required
def result_form(request,pk):
    test=get_object_or_404(TestCase,pk=pk); result=getattr(test,'result',None); form=TestResultForm(request.POST or None,instance=result)
    if request.method=='POST' and form.is_valid():
        x=form.save(commit=False); x.test_case=test; x.created_by=request.user; x.save(); return redirect('object_list',kind='tests')
    return render(request,'form.html',{'form':form,'title':f'{test.code} 결과 등록'})
@login_required
def traceability(request):
    project=get_object_or_404(Project,pk=request.GET.get('project') or Project.objects.values_list('pk',flat=True).first()); rows=trace_rows(project)
    if request.GET.get('gaps')=='1': rows=[r for r in rows if r['status']!='완료']
    return render(request,'traceability.html',{'project':project,'rows':rows})
@login_required
def export(request,fmt):
    project=get_object_or_404(Project,pk=request.GET.get('project') or Project.objects.values_list('pk',flat=True).first()); rows=trace_rows(project)
    if fmt=='xlsx':
        from openpyxl import Workbook
        wb=Workbook(); ws=wb.active; ws.title='Traceability'; ws.append(['요구사항','제목','설계','위험','시험','결과','CAPA','상태'])
        for r in rows: ws.append([r['req'].code,r['req'].title,','.join(x.code for x in r['designs']),','.join(x.code for x in r['risks']),','.join(x.code for x in r['tests']),','.join(getattr(getattr(x,'result',None),'outcome','미등록') for x in r['tests']),','.join(x.code for x in r['capas']),r['status']])
        b=BytesIO(); wb.save(b); data=b.getvalue(); content='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    elif fmt=='docx':
        from docx import Document
        d=Document(); d.add_heading(f'{project.name} 추적성 보고서',0); d.add_paragraph('포트폴리오·교육용 초안 — 담당자 검토 필요')
        for r in rows: d.add_heading(f"{r['req'].code} {r['req'].title}",1); d.add_paragraph(f"상태: {r['status']} / 위험: {', '.join(x.code for x in r['risks']) or '-'} / 시험: {', '.join(x.code for x in r['tests']) or '-'}")
        b=BytesIO(); d.save(b); data=b.getvalue(); content='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    else:
        from reportlab.pdfgen import canvas
        b=BytesIO(); c=canvas.Canvas(b); c.drawString(40,800,'MedTrace RA - Traceability Report'); y=775
        for r in rows: c.drawString(40,y,f"{r['req'].code} | {r['status']}"); y-=18
        c.save(); data=b.getvalue(); content='application/pdf'
    response=HttpResponse(data,content_type=content); response['Content-Disposition']=f'attachment; filename="traceability.{fmt}"'; return response
@admin_required
def audit(request):
    return render(request,'audit.html',{'items':AuditLog.objects.order_by('-created_at')[:200]})
