from .auth import CustomTokenSerializer, CustomTokenView
from .servicio import ServicioSerializer
from .proveedor import ProveedorSerializer
from .compra import CompraSerializer
from .mantenimiento import MantenimientoSerializer
from .user import (
    RegisterSerializer,
    UserSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer,
)

from .marca import MarcaSerializer
from .categoria_moto import CategoriaMotoSerializer
from .moto import MotoSerializer
from .repuesto import RepuestoSerializer
from .movimiento_inventario import MovimientoInventarioSerializer

__all__ = [
    'CustomTokenSerializer',
    'CustomTokenView',
    'RegisterSerializer',
    'UserSerializer',
    'UserProfileSerializer',
    'ChangePasswordSerializer',
    'MarcaSerializer',
    'CategoriaMotoSerializer',
    'MotoSerializer',
    'RepuestoSerializer',
    'MovimientoInventarioSerializer',
    'ProveedorSerializer',
    'ServicioSerializer', 
    'CompraSerializer',
    'MantenimientoSerializer'
]



