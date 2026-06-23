from django.urls import path, include
from rest_framework.routers import DefaultRouter

from motoshop.views.health import health_check

router = DefaultRouter()

urlpatterns = [
    path('health/', health_check),
    path('', include(router.urls)),
]