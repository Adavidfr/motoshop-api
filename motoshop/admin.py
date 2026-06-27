from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from motoshop.models import (
    ClientePerfil,
    CarritoCompras, ItemCarrito,
    Pedido,
    Venta, Financiamiento,
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
