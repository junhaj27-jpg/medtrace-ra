from .models import AuditLog

SENSITIVE_FIELDS = {"password", "password1", "password2", "csrfmiddlewaretoken", "token", "secret"}


def sanitized_request_data(request):
    details = {}
    for key in request.POST:
        if key.lower() in SENSITIVE_FIELDS or "password" in key.lower():
            details[key] = "[REDACTED]"
            continue
        values = request.POST.getlist(key)
        details[key] = values if len(values) > 1 else values[0][:1000]
    if request.FILES:
        details["files"] = {
            key: {"name": upload.name, "size": upload.size, "content_type": upload.content_type}
            for key, upload in request.FILES.items()
        }
    return details


class AuditMiddleware:
    def __init__(self,get_response): self.get_response=get_response
    def __call__(self,request):
        response=self.get_response(request)
        if request.user.is_authenticated and request.method in ('POST','PUT','PATCH','DELETE'):
            AuditLog.objects.create(
                user=request.user,
                action='변경',
                path=request.path[:300],
                method=request.method,
                ip=request.META.get('REMOTE_ADDR'),
                details=sanitized_request_data(request),
                response_status=response.status_code,
            )
        return response
