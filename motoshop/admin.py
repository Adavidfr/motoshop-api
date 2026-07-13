from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from motoshop.models import Proveedor, Servicio
from motoshop.models.compra import Compra
from motoshop.models import Mantenimiento
from motoshop.models import RepuestoMantenimiento
from motoshop.models import (
    ClientePerfil,
    CarritoCompras, ItemCarrito,
    Pedido,
    Venta, Financiamiento,
    Pago, Factura, Garantia, Seguro,
    Notificacion, DocumentoVenta, HistorialEstadoVenta, Devolucion,
)


# ------------------------------------------------------------------ #
#  User Admin                                                           #
# ------------------------------------------------------------------ #

class UserWithRoleAdmin(BaseUserAdmin):
    """Extiende el panel de admin para mostrar el rol del usuario."""
    list_display = ('username', 'email', 'get_role', 'is_staff', 'is_active', 'date_joined')
    list_filter  = ('groups', 'is_staff', 'is_active')

    @admin.display(description='Rol')
    def get_role(self, obj):
        group = obj.groups.first()
        return group.name if group else '—'


admin.site.unregister(User)
admin.site.register(User, UserWithRoleAdmin)


@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'nombre',
        'contacto',
        'telefono',
        'correo',
        'estado',
        'fecha_creacion',
    ]

    list_filter = [
        'estado',
        'fecha_creacion',
    ]

    search_fields = [
        'nombre',
        'contacto',
        'correo',
        'telefono',
    ]

    ordering = [
        'nombre',
    ]
    

@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'nombre',
        'precio_base',
        'tiempo_estimado_minutos',
        'estado',
        'fecha_creacion',
    ]

    list_filter = [
        'estado',
        'fecha_creacion',
    ]

    search_fields = [
        'nombre',
        'descripcion',
    ]

    ordering = [
        'nombre',
    ]
    

@admin.register(Compra)
class CompraAdmin(admin.ModelAdmin):
    list_display = [
        'id_compra',
        'proveedor',
        'moto',
        'repuesto',
        'cantidad',
        'precio_unitario',
        'subtotal',
        'estado',
        'fecha_compra',
    ]

    list_filter = [
        'estado',
        'fecha_compra',
    ]

    search_fields = [
        'proveedor__nombre',
        'moto__modelo',
        'repuesto__nombre',
    ]

    ordering = [
        '-fecha_compra',
    ]
    

@admin.register(Mantenimiento)
class MantenimientoAdmin(admin.ModelAdmin):
    list_display = [
        'id_mantenimiento',
        'moto',
        'usuario_cliente',
        'servicio',
        'kilometraje_actual',
        'costo_final',
        'estado',
        'fecha_registro',
    ]

    list_filter = [
        'estado',
        'fecha_registro',
        'servicio',
    ]

    search_fields = [
        'moto__modelo',
        'usuario_cliente__username',
        'usuario_cliente__email',
        'servicio__nombre',
        'diagnostico_inicial',
    ]

    ordering = [
        '-fecha_registro',
    ]
    

@admin.register(RepuestoMantenimiento)
class RepuestoMantenimientoAdmin(admin.ModelAdmin):
    list_display = [
        'id_repuesto_mantenimiento',
        'mantenimiento',
        'repuesto',
        'cantidad',
        'precio_unitario',
        'subtotal',
    ]

    list_filter = [
        'repuesto',
    ]

    search_fields = [
        'repuesto__nombre',
    ]

    ordering = [
        'id_repuesto_mantenimiento',
    ]


# ------------------------------------------------------------------ #
#  ClientePerfil Admin                                                  #
# ------------------------------------------------------------------ #

@admin.register(ClientePerfil)
class ClientePerfilAdmin(admin.ModelAdmin):
    list_display  = ['id_perfil', 'id_usuario', 'cedula', 'telefono', 'fecha_nacimiento']
    search_fields = ['id_usuario__username', 'id_usuario__email', 'cedula']
    raw_id_fields = ['id_usuario']


# ------------------------------------------------------------------ #
#  Carrito Admin                                                        #
# ------------------------------------------------------------------ #

class ItemCarritoInline(admin.TabularInline):
    model  = ItemCarrito
    extra  = 0
    fields = ['id_moto', 'id_repuesto', 'cantidad', 'precio_unitario', 'subtotal']
    readonly_fields = ['subtotal']


@admin.register(CarritoCompras)
class CarritoComprasAdmin(admin.ModelAdmin):
    list_display    = ['id_carrito', 'id_usuario_cliente', 'estado', 'fecha_creacion']
    list_filter     = ['estado']
    search_fields   = ['id_usuario_cliente__username']
    inlines         = [ItemCarritoInline]
    readonly_fields = ['fecha_creacion']


# ------------------------------------------------------------------ #
#  Pedido Admin                                                         #
# ------------------------------------------------------------------ #

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display    = ['id_pedido', 'id_usuario_cliente', 'id_carrito', 'estado', 'total', 'fecha_pedido']
    list_filter     = ['estado']
    search_fields   = ['id_usuario_cliente__username']
    readonly_fields = ['total', 'fecha_pedido']


# ------------------------------------------------------------------ #
#  Venta Admin                                                          #
# ------------------------------------------------------------------ #

class FinanciamientoInline(admin.TabularInline):
    model  = Financiamiento
    extra  = 0
    fields = ['entidad_financiera', 'monto_financiado', 'tasa_interes', 'plazo_meses', 'cuota_mensual', 'estado']


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display    = ['id_venta', 'id_pedido', 'id_usuario_cliente', 'id_usuario_vendedor', 'total_venta', 'estado', 'fecha_venta']
    list_filter     = ['estado']
    search_fields   = ['id_usuario_cliente__username', 'id_usuario_vendedor__username']
    inlines         = [FinanciamientoInline]
    readonly_fields = ['fecha_venta']


# ------------------------------------------------------------------ #
#  Financiamiento Admin                                                 #
# ------------------------------------------------------------------ #

@admin.register(Financiamiento)
class FinanciamientoAdmin(admin.ModelAdmin):
    list_display  = ['id_financiamiento', 'id_venta', 'entidad_financiera', 'monto_financiado', 'plazo_meses', 'cuota_mensual', 'estado']
    list_filter   = ['estado', 'entidad_financiera']
    search_fields = ['id_venta__id_venta', 'entidad_financiera']


# ------------------------------------------------------------------ #
#  Pago Admin                                                           #
# ------------------------------------------------------------------ #

@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display  = ['id_pago', 'id_venta', 'monto', 'metodo_pago', 'estado', 'fecha_pago']
    list_filter   = ['estado', 'metodo_pago', 'fecha_pago']
    search_fields = ['referencia']
    ordering      = ['-fecha_pago']


# ------------------------------------------------------------------ #
#  Factura Admin                                                        #
# ------------------------------------------------------------------ #

@admin.register(Factura)
class FacturaAdmin(admin.ModelAdmin):
    list_display  = ['id_factura', 'id_venta', 'numero_factura', 'subtotal', 'iva', 'total', 'fecha_emision']
    list_filter   = ['fecha_emision']
    search_fields = ['numero_factura']
    ordering      = ['-fecha_emision']


# ------------------------------------------------------------------ #
#  Garantia Admin                                                       #
# ------------------------------------------------------------------ #

@admin.register(Garantia)
class GarantiaAdmin(admin.ModelAdmin):
    list_display  = ['id_garantia', 'id_venta', 'id_moto', 'meses_garantia', 'fecha_inicio', 'fecha_fin', 'estado']
    list_filter   = ['estado', 'fecha_inicio']
    ordering      = ['-fecha_inicio']


# ------------------------------------------------------------------ #
#  Seguro Admin                                                         #
# ------------------------------------------------------------------ #

@admin.register(Seguro)
class SeguroAdmin(admin.ModelAdmin):
    list_display  = ['id_seguro', 'id_venta', 'aseguradora', 'numero_poliza', 'tipo_cobertura', 'fecha_inicio', 'fecha_fin', 'estado']
    list_filter   = ['estado', 'tipo_cobertura']
    search_fields = ['aseguradora', 'numero_poliza']
    ordering      = ['-fecha_inicio']


# ------------------------------------------------------------------ #
#  Notificacion Admin                                                   #
# ------------------------------------------------------------------ #

@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display  = ['id_notificacion', 'id_usuario', 'titulo', 'leido', 'fecha_creacion']
    list_filter   = ['leido', 'fecha_creacion']
    search_fields = ['titulo', 'mensaje', 'id_usuario__username']
    ordering      = ['-fecha_creacion']


# ------------------------------------------------------------------ #
#  DocumentoVenta Admin                                                 #
# ------------------------------------------------------------------ #

@admin.register(DocumentoVenta)
class DocumentoVentaAdmin(admin.ModelAdmin):
    list_display  = ['id_documento', 'id_venta', 'tipo_documento', 'archivo_url', 'fecha_subida']
    list_filter   = ['tipo_documento', 'fecha_subida']
    search_fields = ['archivo_url']
    ordering      = ['-fecha_subida']


# ------------------------------------------------------------------ #
#  HistorialEstadoVenta Admin                                           #
# ------------------------------------------------------------------ #

@admin.register(HistorialEstadoVenta)
class HistorialEstadoVentaAdmin(admin.ModelAdmin):
    list_display  = ['id_historial', 'id_venta', 'estado_anterior', 'estado_nuevo', 'fecha_cambio']
    list_filter   = ['estado_nuevo', 'fecha_cambio']
    search_fields = ['observacion']
    ordering      = ['-fecha_cambio']


# ------------------------------------------------------------------ #
#  Devolucion Admin                                                     #
# ------------------------------------------------------------------ #

@admin.register(Devolucion)
class DevolucionAdmin(admin.ModelAdmin):
    list_display  = ['id_devolucion', 'id_venta', 'estado', 'monto_devolucion', 'fecha_solicitud', 'fecha_resolucion']
    list_filter   = ['estado', 'fecha_solicitud']
    search_fields = ['motivo']
    ordering      = ['-fecha_solicitud']


# ------------------------------------------------------------------ #
#  Catalogo e Inventario Admin (Andrés)                                #
# ------------------------------------------------------------------ #

from motoshop.models.marca import Marca
from motoshop.models.categoria_moto import CategoriaMoto
from motoshop.models.moto import Moto
from motoshop.models.repuesto import Repuesto
from motoshop.models.movimiento_inventario import MovimientoInventario

@admin.register(Marca)
class MarcaAdmin(admin.ModelAdmin):
    list_display  = ['id_marca', 'nombre', 'estado']
    search_fields = ['nombre']

@admin.register(CategoriaMoto)
class CategoriaMotoAdmin(admin.ModelAdmin):
    list_display  = ['id_categoria', 'nombre', 'estado']
    search_fields = ['nombre']

@admin.register(Moto)
class MotoAdmin(admin.ModelAdmin):
    list_display  = ['id_moto', 'modelo', 'marca', 'categoria', 'precio', 'stock', 'estado']
    list_filter   = ['estado', 'marca', 'categoria']
    search_fields = ['modelo']

@admin.register(Repuesto)
class RepuestoAdmin(admin.ModelAdmin):
    list_display  = ['id_repuesto', 'nombre', 'sku', 'precio_venta', 'stock', 'estado']
    list_filter   = ['estado']
    search_fields = ['nombre', 'sku']

@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    list_display  = ['id_movimiento', 'tipo_movimiento', 'cantidad', 'fecha_movimiento']
    list_filter   = ['tipo_movimiento']


