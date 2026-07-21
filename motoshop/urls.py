from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from motoshop.views.health import health_check
from motoshop.views.mantenimiento import MantenimientoViewSet
from motoshop.views.proveedor import ProveedorViewSet
from motoshop.views.repuesto_mantenimiento import RepuestoMantenimientoViewSet
from motoshop.views.servicio import ServicioViewSet
from motoshop.views.compra import CompraViewSet
from motoshop.views.auth import (
    RegisterView,
    LogoutView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
)
from motoshop.views.newsletter import NewsletterSubscribeView
from motoshop.views.user import UserViewSet
from motoshop.views.cliente import ClientePerfilView, ClientePerfilAdminListView
from motoshop.views.carrito_compras import CarritoComprasViewSet
from motoshop.views.item_carrito import ItemsCarritoViewSet
from motoshop.views.pedido import PedidoViewSet
from motoshop.views.venta import VentaViewSet
from motoshop.views.financiamiento import FinanciamientoViewSet
from motoshop.views import (
    MarcaViewSet,
    CategoriaMotoViewSet,
    MotoViewSet,
    RepuestoViewSet,
    MovimientoInventarioViewSet,
)
from motoshop.views.financiamiento import FinanciamientoViewSet
from motoshop.views.pago import PagoViewSet
from motoshop.views.factura import FacturaViewSet
from motoshop.views.garantia import GarantiaViewSet
from motoshop.views.seguro import SeguroViewSet
from motoshop.views.notificacion import NotificacionViewSet
from motoshop.views.documento_venta import DocumentoVentaViewSet
from motoshop.views.historial_estado_venta import HistorialEstadoVentaViewSet
from motoshop.views.devolucion import DevolucionViewSet
from motoshop.serializers.auth import CustomTokenView

router = DefaultRouter()
router.register('users',                    UserViewSet,                  basename='user')
router.register('marcas',                   MarcaViewSet,                 basename='marca')
router.register('categorias-moto',          CategoriaMotoViewSet,         basename='categoria-moto')
router.register('motos',                    MotoViewSet,                  basename='moto')
router.register('repuestos',                RepuestoViewSet,              basename='repuesto')
router.register('movimientos-inventario',   MovimientoInventarioViewSet,  basename='movimiento-inventario')
router.register('proveedores',              ProveedorViewSet,             basename='proveedores')
router.register('servicios',               ServicioViewSet,              basename='servicios')
router.register('compras',                  CompraViewSet,                basename='compras')
router.register('mantenimientos',           MantenimientoViewSet,         basename='mantenimientos')
router.register('repuestos-mantenimiento',  RepuestoMantenimientoViewSet, basename='repuestos-mantenimiento')
router.register('carritos',                 CarritoComprasViewSet,        basename='carrito')
router.register('items-carrito',            ItemsCarritoViewSet,          basename='item-carrito')
router.register('pedidos',                  PedidoViewSet,                basename='pedido')
router.register('ventas',                   VentaViewSet,                 basename='venta')
router.register('financiamientos',          FinanciamientoViewSet,        basename='financiamiento')
router.register('pagos',                    PagoViewSet,                  basename='pago')
router.register('facturas',                 FacturaViewSet,               basename='factura')
router.register('garantias',               GarantiaViewSet,              basename='garantia')
router.register('seguros',                  SeguroViewSet,                basename='seguro')
router.register('notificaciones',           NotificacionViewSet,          basename='notificacion')
router.register('documentos-venta',         DocumentoVentaViewSet,        basename='documento-venta')
router.register('historial-estado-venta',   HistorialEstadoVentaViewSet,  basename='historial-estado-venta')
router.register('devoluciones',             DevolucionViewSet,            basename='devolucion')

urlpatterns = [
    # Health check
    path('health/',             health_check),

    # Auth
    path('auth/register/',      RegisterView.as_view()),
    path('auth/login/',         CustomTokenView.as_view()),
    path('auth/token/refresh/', TokenRefreshView.as_view()),
    path('auth/token/verify/',  TokenVerifyView.as_view()),
    path('auth/logout/',        LogoutView.as_view()),
    
    # Password Reset
    path('auth/password-reset/',         PasswordResetRequestView.as_view()),
    path('auth/password-reset-confirm/', PasswordResetConfirmView.as_view()),
    
    # Newsletter
    path('newsletter/subscribe/',        NewsletterSubscribeView.as_view()),

    # Perfil del cliente (APIView, no ViewSet)
    path('clientes/perfil/',    ClientePerfilView.as_view()),
    path('clientes/',           ClientePerfilAdminListView.as_view()),

    # ViewSets registrados en el router
    path('', include(router.urls)),
]