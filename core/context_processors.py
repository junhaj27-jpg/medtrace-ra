from .permissions import ROLE_LABELS,can_modify,has_full_access,user_role
def access_flags(request):
    role=user_role(request.user)
    return {'has_full_access':has_full_access(request.user),'can_modify':can_modify(request.user),'user_role':role,'user_role_label':ROLE_LABELS.get(role,'')}

