from .permissions import has_full_access
def access_flags(request): return {'has_full_access':has_full_access(request.user)}

