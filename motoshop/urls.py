from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from motoshop.views.health         import health_check
from motoshop.views.auth           import RegisterView, LogoutView
from motoshop.views.user           import UserViewSet
from motoshop.views.cliente        import ClientePerfilView, ClientePerfilAdminListView
from motoshop.views.carrito_compras    import CarritoComprasViewSet
from motoshop.views.item_carrito   import ItemsCarritoViewSet
from motoshop.views.pedido         import PedidoViewSet
from motoshop.views.venta          import VentaViewSet
from motoshop.views.financiamiento import FinanciamientoViewSet
from motoshop.serializers.auth     import CustomTokenView

router = DefaultRouter()
router.register('users',           UserViewSet,          basename='user')
router.register('carritos',        CarritoComprasViewSet, basename='carrito')
router.register('items-carrito',   ItemsCarritoViewSet,   basename='item-carrito')
router.register('pedidos',         PedidoViewSet,        basename='pedido')
router.register('ventas',          VentaViewSet,         basename='venta')
router.register('financiamientos', FinanciamientoViewSet, basename='financiamiento')

urlpatterns = [
    # Health check
    path('health/',             health_check),

    # Auth
    path('auth/register/',      RegisterView.as_view()),
    path('auth/login/',         CustomTokenView.as_view()),
    path('auth/token/refresh/', TokenRefreshView.as_view()),
    path('auth/token/verify/',  TokenVerifyView.as_view()),
    path('auth/logout/',        LogoutView.as_view()),

    # Perfil del cliente (APIView, no ViewSet)
    path('clientes/perfil/',    ClientePerfilView.as_view()),
    path('clientes/',           ClientePerfilAdminListView.as_view()),

    # ViewSets registrados en el router
    path('', include(router.urls)),
]