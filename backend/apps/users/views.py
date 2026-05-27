from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from django.contrib.auth import get_user_model
from apps.users.serializers import CustomTokenObtainPairSerializer, UserSerializer

User = get_user_model()

class CookieTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            return Response({
                "errors": [{
                    "code": "VALIDATION_ERROR",
                    "field": "credentials",
                    "message": "Invalid email or password."
                }],
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        response = Response({
            "data": {
                "message": "Authentication successful",
                "user": UserSerializer(serializer.user).data
            },
            "errors": []
        }, status=status.HTTP_200_OK)
        
        access_token = serializer.validated_data.get('access')
        refresh_token = serializer.validated_data.get('refresh')
        
        # Set access token cookie (60 minutes)
        response.set_cookie(
            'access_token',
            access_token,
            max_age=3600,
            httponly=True,
            secure=not settings.DEBUG,
            samesite='Lax'
        )
        
        # Set refresh token cookie (7 days)
        response.set_cookie(
            'refresh_token',
            refresh_token,
            max_age=7 * 24 * 3600,
            httponly=True,
            secure=not settings.DEBUG,
            samesite='Lax'
        )
        
        return response

class CookieTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh_token')
        if not refresh_token:
            return Response({
                "errors": [{
                    "code": "VALIDATION_ERROR",
                    "field": "refresh_token",
                    "message": "Refresh token is missing from cookies."
                }],
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Inject the refresh token from cookies into request data for the serializer
        data = request.data.copy()
        data['refresh'] = refresh_token
        serializer = self.get_serializer(data=data)
        
        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
            return Response({
                "errors": [{
                    "code": "VALIDATION_ERROR",
                    "field": "refresh_token",
                    "message": "Invalid or expired refresh token."
                }],
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
            
        response = Response({
            "data": {
                "message": "Token refreshed successfully"
            },
            "errors": []
        }, status=status.HTTP_200_OK)
        
        access_token = serializer.validated_data.get('access')
        response.set_cookie(
            'access_token',
            access_token,
            max_age=3600,
            httponly=True,
            secure=not settings.DEBUG,
            samesite='Lax'
        )
        
        new_refresh = serializer.validated_data.get('refresh')
        if new_refresh:
            response.set_cookie(
                'refresh_token',
                new_refresh,
                max_age=7 * 24 * 3600,
                httponly=True,
                secure=not settings.DEBUG,
                samesite='Lax'
            )
            
        return response

class LogoutView(APIView):
    def post(self, request, *args, **kwargs):
        response = Response({
            "data": {
                "message": "Logged out successfully"
            },
            "errors": []
        }, status=status.HTTP_200_OK)
        
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response

class UserMeView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response({
            "data": serializer.data,
            "errors": []
        }, status=status.HTTP_200_OK)
