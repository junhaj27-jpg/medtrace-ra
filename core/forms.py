from django import forms
from .models import Project,Requirement,DesignItem,Risk,TestCase,TestResult,Incident,CAPA
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

