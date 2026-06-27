from .health import health_check
from .auth import RegisterView, LogoutView
from .user import UserViewSet
from .marca import MarcaViewSet
from .categoria_moto import CategoriaMotoViewSet
from .moto import MotoViewSet
from .repuesto import RepuestoViewSet
from .movimiento_inventario import MovimientoInventarioViewSet
from .proveedor import ProveedorViewSet
from .servicio import ServicioViewSet
from .compra import CompraViewSet
from .mantenimiento import MantenimientoViewSet
from .repuesto_mantenimiento import RepuestoMantenimientoViewSet
__all__ = [
    'health_check',
    'RegisterView',
    'LogoutView',
    'UserViewSet',
    'MarcaViewSet',
    'CategoriaMotoViewSet',
    'MotoViewSet',
    'RepuestoViewSet',
    'MovimientoInventarioViewSet',
    'ProveedorViewSet',
    'ServicioViewSet', 
    'CompraViewSet', 
    'MantenimientoViewSet', 
    'RepuestoMantenimientoViewSet'
]

