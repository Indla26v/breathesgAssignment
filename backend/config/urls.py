from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('apps.users.urls')),
    path('api/v1/', include('apps.ingestion.urls')),
    path('api/v1/', include('apps.review.urls')),
    path('api/v1/', include('apps.audit.urls')),
]
