from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from motoshop.views.health import health_check
from motoshop.views.mantenimiento import MantenimientoViewSet
from motoshop.views.proveedor import ProveedorViewSet
from motoshop.views.repuesto_mantenimiento import RepuestoMantenimientoViewSet
from motoshop.views.servicio import ServicioViewSet
from motoshop.views.compra import CompraViewSet
from motoshop.views.auth   import RegisterView, LogoutView
from motoshop.views import (
    UserViewSet,
    MarcaViewSet,
    CategoriaMotoViewSet,
    MotoViewSet,
    RepuestoViewSet,
    MovimientoInventarioViewSet
)
from motoshop.serializers.auth import CustomTokenView

router = DefaultRouter()
router.register('users', UserViewSet, basename='user')
router.register('marcas', MarcaViewSet, basename='marca')
router.register('categorias-moto', CategoriaMotoViewSet, basename='categoria-moto')
router.register('motos', MotoViewSet, basename='moto')
router.register('repuestos', RepuestoViewSet, basename='repuesto')
router.register('movimientos-inventario', MovimientoInventarioViewSet, basename='movimiento-inventario')
router.register('proveedores', ProveedorViewSet, basename='proveedores')
router.register('servicios', ServicioViewSet, basename='servicios')
router.register('compras', CompraViewSet, basename='compras')
router.register('mantenimientos', MantenimientoViewSet, basename='mantenimientos')
router.register('repuestos-mantenimiento',RepuestoMantenimientoViewSet,basename='repuestos-mantenimiento')


urlpatterns = [
    path('health/',             health_check),
    path('auth/register/',      RegisterView.as_view()),
    path('auth/login/',         CustomTokenView.as_view()),
    path('auth/token/refresh/', TokenRefreshView.as_view()),
    path('auth/token/verify/',  TokenVerifyView.as_view()),
    path('auth/logout/',        LogoutView.as_view()),
    path('', include(router.urls)),
]