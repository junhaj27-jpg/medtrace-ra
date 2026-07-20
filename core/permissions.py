from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib.auth.views import redirect_to_login
from rest_framework.permissions import BasePermission, SAFE_METHODS

def has_full_access(user):
    return bool(user and user.is_authenticated and (user.is_superuser or user.groups.filter(name='ADMIN').exists()))

def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request,*args,**kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if has_full_access(request.user):
            return view_func(request,*args,**kwargs)
        raise PermissionDenied
    return wrapper

class IsSystemAdmin(BasePermission):
    def has_permission(self,request,view): return has_full_access(request.user)

class RoleBasedAccess(BasePermission):
    """인증 사용자는 조회, 업무 역할은 변경, 시스템 관리자는 항상 허용."""
    def has_permission(self,request,view):
        user=request.user
        if not user or not user.is_authenticated:return False
        if has_full_access(user) or request.method in SAFE_METHODS:return True
        return user.groups.filter(name__in=['RA_MANAGER','DEVELOPER','TESTER']).exists()

