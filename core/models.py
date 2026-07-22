from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL, related_name="+")

    class Meta:
        abstract = True


class Project(TimestampedModel):
    STATUS_CHOICES = [(x, x) for x in ("기획", "개발", "검증", "인허가 준비", "완료", "중단")]
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=160)
    device_name = models.CharField(max_length=160)
    device_class = models.CharField(max_length=40, blank=True)
    model_name = models.CharField(max_length=100, blank=True)
    manager = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL, related_name="managed_projects")
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="개발")
    start_date = models.DateField(blank=True, null=True)
    target_date = models.DateField(blank=True, null=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.code} {self.name}"


class ProjectCodeModel(TimestampedModel):
    code_prefix = "ITEM"
    code = models.CharField(max_length=20)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.code:
            latest = type(self).objects.filter(project=self.project).order_by("-pk").values_list("code", flat=True).first()
            number = 1
            if latest and latest.startswith(f"{self.code_prefix}-"):
                try:
                    number = int(latest.rsplit("-", 1)[1]) + 1
                except ValueError:
                    pass
            self.code = f"{self.code_prefix}-{number:03d}"
        super().save(*args, **kwargs)


class Requirement(ProjectCodeModel):
    code_prefix = "REQ"
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="requirements")
    title = models.CharField(max_length=200)
    description = models.TextField()
    req_type = models.CharField(max_length=40, default="기능 요구사항")
    source = models.CharField(max_length=40, default="내부 검토")
    priority = models.CharField(max_length=10, default="중")
    status = models.CharField(max_length=20, default="초안")
    version = models.PositiveIntegerField(default=1)
    assignee = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL, related_name="+")

    class Meta:
        unique_together = ("project", "code")

    def __str__(self):
        return f"{self.code} {self.title}"


class DesignItem(ProjectCodeModel):
    code_prefix = "DES"
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="designs")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    design_type = models.CharField(max_length=40, default="소프트웨어")
    status = models.CharField(max_length=20, default="초안")
    version = models.PositiveIntegerField(default=1)
    document_name = models.CharField(max_length=200, blank=True)
    requirements = models.ManyToManyField(Requirement, blank=True, related_name="designs")

    class Meta:
        unique_together = ("project", "code")

    def __str__(self):
        return f"{self.code} {self.title}"


class Risk(ProjectCodeModel):
    code_prefix = "RISK"
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="risks")
    hazard = models.CharField(max_length=200)
    sequence = models.TextField(blank=True)
    hazardous_situation = models.TextField(blank=True)
    harm = models.TextField(blank=True)
    probability = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    severity = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    control = models.TextField(blank=True)
    residual_probability = models.IntegerField(blank=True, null=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
    residual_severity = models.IntegerField(blank=True, null=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
    residual_acceptable = models.BooleanField(default=False)
    status = models.CharField(max_length=20, default="초안")
    requirements = models.ManyToManyField(Requirement, blank=True, related_name="risks")
    designs = models.ManyToManyField(DesignItem, blank=True, related_name="risks")

    class Meta:
        unique_together = ("project", "code")

    @property
    def score(self):
        return self.probability * self.severity

    @property
    def residual_score(self):
        if self.residual_probability is None or self.residual_severity is None:
            return None
        return self.residual_probability * self.residual_severity

    @property
    def level(self):
        return "높음" if self.score >= 10 else "중간" if self.score >= 5 else "낮음"

    def __str__(self):
        return f"{self.code} {self.hazard}"


class TestCase(ProjectCodeModel):
    code_prefix = "TEST"
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tests")
    name = models.CharField(max_length=200)
    purpose = models.TextField(blank=True)
    precondition = models.TextField(blank=True)
    procedure = models.TextField()
    expected = models.TextField()
    test_type = models.CharField(max_length=40, default="시스템시험")
    assignee = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL, related_name="+")
    requirements = models.ManyToManyField(Requirement, blank=True, related_name="tests")
    risks = models.ManyToManyField(Risk, blank=True, related_name="tests")

    class Meta:
        unique_together = ("project", "code")

    def __str__(self):
        return f"{self.code} {self.name}"


class Incident(ProjectCodeModel):
    code_prefix = "INC"
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="incidents")
    title = models.CharField(max_length=200)
    occurred_at = models.DateField()
    description = models.TextField()
    severity = models.IntegerField(default=3, validators=[MinValueValidator(1), MaxValueValidator(5)])
    investigation_status = models.CharField(max_length=30, default="접수")
    reporting_review = models.CharField(max_length=40, default="검토 필요")
    risks = models.ManyToManyField(Risk, blank=True)
    related_test = models.ForeignKey(TestCase, blank=True, null=True, on_delete=models.SET_NULL)

    class Meta:
        unique_together = ("project", "code")

    def __str__(self):
        return f"{self.code} {self.title}"


class TestResult(TimestampedModel):
    OUTCOME_CHOICES = [("PASS", "PASS"), ("FAIL", "FAIL")]
    test_case = models.OneToOneField(TestCase, on_delete=models.CASCADE, related_name="result")
    actual = models.TextField()
    outcome = models.CharField(max_length=10, choices=OUTCOME_CHOICES)
    tested_at = models.DateField()
    tester = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL, related_name="+")
    note = models.TextField(blank=True)

    def __str__(self):
        return f"{self.test_case.code} {self.outcome}"


class CAPA(ProjectCodeModel):
    code_prefix = "CAPA"
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="capas")
    title = models.CharField(max_length=200)
    capa_type = models.CharField(max_length=30, default="시정 및 예방조치")
    cause = models.TextField()
    corrective_action = models.TextField()
    preventive_action = models.TextField(blank=True)
    target_date = models.DateField()
    completed_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=30, default="초안")
    effectiveness_method = models.TextField(blank=True)
    effectiveness_result = models.TextField(blank=True)
    incident = models.ForeignKey(Incident, blank=True, null=True, on_delete=models.SET_NULL, related_name="capas")
    risk = models.ForeignKey(Risk, blank=True, null=True, on_delete=models.SET_NULL, related_name="capas")
    test_case = models.ForeignKey(TestCase, blank=True, null=True, on_delete=models.SET_NULL, related_name="capas")

    class Meta:
        unique_together = ("project", "code")

    @property
    def overdue(self):
        return self.target_date < timezone.localdate() and self.status not in ("완료", "취소")

    def __str__(self):
        return f"{self.code} {self.title}"


class AuditLog(models.Model):
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=30)
    path = models.CharField(max_length=300)
    method = models.CharField(max_length=10)
    ip = models.GenericIPAddressField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.created_at} {self.user} {self.method} {self.path}"
