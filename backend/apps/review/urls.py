from django.urls import path, include
from rest_framework.routers import SimpleRouter
from apps.review.views import NormalizedRecordViewSet, DashboardSummaryView

router = SimpleRouter()
router.register('records', NormalizedRecordViewSet, basename='record')

urlpatterns = [
    path('dashboard/summary/', DashboardSummaryView.as_view(), name='dashboard_summary'),
    path('', include(router.urls)),
]
