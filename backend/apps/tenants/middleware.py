import contextvars
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from rest_framework_simplejwt.tokens import UntypedToken
from apps.tenants.models import Tenant

# Context variables for thread-safe/async-safe request state
_current_tenant = contextvars.ContextVar('current_tenant', default=None)
_bypass_tenant_filter = contextvars.ContextVar('bypass_tenant_filter', default=False)
_current_user_role = contextvars.ContextVar('current_user_role', default=None)

def get_current_tenant():
    return _current_tenant.get()

def set_current_tenant(tenant):
    _current_tenant.set(tenant)

def get_bypass_tenant_filter():
    return _bypass_tenant_filter.get()

def set_bypass_tenant_filter(bypass):
    _bypass_tenant_filter.set(bypass)

def get_current_user_role():
    return _current_user_role.get()

class TenantMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Reset context variables for this request
        _current_tenant.set(None)
        _bypass_tenant_filter.set(False)
        _current_user_role.set(None)
        request.tenant = None

        # Resolve token from header or cookies
        token_str = None
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            parts = auth_header.split(' ')
            if len(parts) == 2:
                token_str = parts[1]
        elif 'access_token' in request.COOKIES:
            token_str = request.COOKIES['access_token']

        path = request.path
        # Exclude auth endpoints, admin site, and static assets from enforcement
        is_public = (
            path.startswith('/api/v1/auth/') or 
            path.startswith('/admin/') or 
            path.startswith('/static/') or
            path.startswith('/media/')
        )

        if token_str:
            try:
                # UntypedToken decodes and validates signature, but doesn't check user existence
                token = UntypedToken(token_str)
                tenant_id = token.get('tenant_id')
                role = token.get('role')
                
                if tenant_id:
                    try:
                        tenant = Tenant.objects.get(id=tenant_id, is_active=True)
                        _current_tenant.set(tenant)
                        request.tenant = tenant
                    except Tenant.DoesNotExist:
                        if not is_public:
                            return JsonResponse({
                                "errors": [{
                                    "code": "FORBIDDEN",
                                    "field": None,
                                    "message": "Tenant is inactive or does not exist."
                                }],
                                "data": None
                            }, status=403)
                
                if role:
                    _current_user_role.set(role)
                    if role == 'PLATFORM_ADMIN':
                        _bypass_tenant_filter.set(True)

            except Exception as e:
                if not is_public and path.startswith('/api/v1/'):
                    return JsonResponse({
                        "errors": [{
                            "code": "UNAUTHORIZED",
                            "field": None,
                            "message": f"Invalid token or session expired: {str(e)}"
                        }],
                        "data": None
                    }, status=401)
        else:
            # Request lacks token
            if not is_public and path.startswith('/api/v1/'):
                return JsonResponse({
                    "errors": [{
                        "code": "UNAUTHORIZED",
                        "field": None,
                        "message": "Authentication token required."
                    }],
                    "data": None
                }, status=401)
        
        return None
