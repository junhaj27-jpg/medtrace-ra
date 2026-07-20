from .models import AuditLog
class AuditMiddleware:
    def __init__(self,get_response): self.get_response=get_response
    def __call__(self,request):
        response=self.get_response(request)
        if request.user.is_authenticated and request.method in ('POST','PUT','PATCH','DELETE'):
            AuditLog.objects.create(user=request.user,action='변경',path=request.path[:300],method=request.method,ip=request.META.get('REMOTE_ADDR'))
        return response
