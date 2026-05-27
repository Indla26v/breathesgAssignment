from django.urls import path, include
from rest_framework.routers import SimpleRouter
from apps.ingestion.views import BatchViewSet

router = SimpleRouter()
router.register('batches', BatchViewSet, basename='batch')

urlpatterns = [
    path('', include(router.urls)),
]
