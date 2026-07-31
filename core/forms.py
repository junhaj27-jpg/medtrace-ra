from django import forms
from django.contrib.auth.models import User
from .models import Project,Requirement,DesignItem,Risk,TestCase,TestResult,Incident,CAPA,ChangeRequest
from .permissions import ROLE_LABELS
class DateInput(forms.DateInput): input_type='date'
class ModelForm(forms.ModelForm):
    def __init__(self,*a,**k):
        super().__init__(*a,**k)
        for f in self.fields.values(): f.widget.attrs['class']='field'
class ProjectForm(ModelForm):
    class Meta: model=Project; exclude=('created_by',); widgets={'start_date':DateInput(),'target_date':DateInput()}
class RequirementForm(ModelForm):
    class Meta: model=Requirement; exclude=('created_by','project'); widgets={'description':forms.Textarea(attrs={'rows':4})}
class DesignItemForm(ModelForm):
    class Meta: model=DesignItem; exclude=('created_by','project')
class RiskForm(ModelForm):
    class Meta: model=Risk; exclude=('created_by','project')
class TestCaseForm(ModelForm):
    class Meta: model=TestCase; exclude=('created_by','project')
class TestResultForm(ModelForm):
    class Meta: model=TestResult; exclude=('created_by','test_case'); widgets={'tested_at':DateInput()}
class IncidentForm(ModelForm):
    class Meta: model=Incident; exclude=('created_by','project'); widgets={'occurred_at':DateInput()}
class CAPAForm(ModelForm):
    class Meta: model=CAPA; exclude=('created_by','project'); widgets={'target_date':DateInput(),'completed_date':DateInput()}
class ChangeRequestForm(ModelForm):
    class Meta:
        model=ChangeRequest
        exclude=('created_by','project','reviewed_by','reviewed_at')
        widgets={'reason':forms.Textarea(attrs={'rows':4}),'impact':forms.Textarea(attrs={'rows':4})}
    def clean_status(self):
        status=self.cleaned_data['status']
        if status=='승인' and not (self.instance.pk and hasattr(self.instance,'approval_signature')):
            raise forms.ValidationError('승인은 목록의 전자서명 기능을 사용해야 합니다.')
        return status

class ApprovalSignatureForm(forms.Form):
    password=forms.CharField(label='현재 비밀번호',widget=forms.PasswordInput)
    comment=forms.CharField(label='승인 의견',required=False,widget=forms.Textarea(attrs={'rows':4}))
    confirm=forms.BooleanField(label='현재 내용과 버전을 검토했으며 승인합니다.')
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        for field in self.fields.values(): field.widget.attrs['class']='field'

class RequirementImportForm(forms.Form):
    project=forms.ModelChoiceField(queryset=Project.objects.all(),label='프로젝트')
    file=forms.FileField(label='Excel 파일 (.xlsx)')

class ManagedUserForm(forms.Form):
    username=forms.CharField(label='사용자명',max_length=150)
    email=forms.EmailField(label='이메일',required=False)
    role=forms.ChoiceField(label='역할',choices=list(ROLE_LABELS.items()))
    password=forms.CharField(label='비밀번호',required=False,widget=forms.PasswordInput,help_text='신규 사용자는 8자 이상, 기존 사용자는 변경할 때만 입력')
    is_active=forms.BooleanField(label='활성 계정',required=False,initial=True)
    def __init__(self,*args,user_instance=None,**kwargs):
        self.user_instance=user_instance
        super().__init__(*args,**kwargs)
        for field in self.fields.values(): field.widget.attrs['class']='field'
    def clean_username(self):
        username=self.cleaned_data['username']
        qs=User.objects.filter(username=username)
        if self.user_instance: qs=qs.exclude(pk=self.user_instance.pk)
        if qs.exists(): raise forms.ValidationError('이미 사용 중인 사용자명입니다.')
        return username
    def clean_password(self):
        password=self.cleaned_data.get('password','')
        if not self.user_instance and len(password)<8: raise forms.ValidationError('신규 사용자의 비밀번호는 8자 이상이어야 합니다.')
        if password and len(password)<8: raise forms.ValidationError('비밀번호는 8자 이상이어야 합니다.')
        return password

