from rest_framework_simplejwt.authentication import JWTAuthentication

class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        # 1. Try default Header Authentication
        header = self.get_header(request)
        if header is None:
            # 2. Fallback to HttpOnly Cookie Authentication
            raw_token = request.COOKIES.get('access_token')
            if raw_token is not None:
                try:
                    validated_token = self.get_validated_token(raw_token)
                    return self.get_user(validated_token), validated_token
                except Exception:
                    # Ignore invalid token here; it will trigger 401 in permission checks if route is protected
                    return None
            return None
        
        # Parse from header
        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None
            
        validated_token = self.get_validated_token(raw_token)
        return self.get_user(validated_token), validated_token
