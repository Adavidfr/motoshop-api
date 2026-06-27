from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from motoshop.models import Proveedor, Servicio
from motoshop.models.compra import Compra
from motoshop.models import Mantenimiento
from motoshop.models import RepuestoMantenimiento
class UserWithRoleAdmin(BaseUserAdmin):
    """
    Extiende el panel de admin para mostrar el rol del usuario.
    """
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