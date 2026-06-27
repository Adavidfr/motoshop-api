import django_filters
from motoshop.models import Proveedor,Servicio, Compra, Mantenimiento
from motoshop.models.repuesto_mantenimiento import RepuestoMantenimiento


class ProveedorFilter(django_filters.FilterSet):
    nombre = django_filters.CharFilter(lookup_expr='icontains')
    contacto = django_filters.CharFilter(lookup_expr='icontains')
    correo = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Proveedor
        fields = ['estado']
        

class ServicioFilter(django_filters.FilterSet):
    nombre = django_filters.CharFilter(lookup_expr='icontains')
    descripcion = django_filters.CharFilter(lookup_expr='icontains')
    precio_base = django_filters.NumberFilter()

    class Meta:
        model = Servicio
        fields = ['estado']
        
class CompraFilter(django_filters.FilterSet):
    estado = django_filters.CharFilter(lookup_expr='icontains')

    fecha_compra = django_filters.DateFromToRangeFilter()

    class Meta:
        model = Compra
        fields = [
            'proveedor',
            'moto',
            'repuesto',
            'estado',
            'fecha_compra',
        ]
        
class MantenimientoFilter(django_filters.FilterSet):
    estado = django_filters.CharFilter(lookup_expr='icontains')
    fecha_registro = django_filters.DateFromToRangeFilter()

    class Meta:
        model = Mantenimiento
        fields = [
            'moto',
            'usuario_cliente',
            'servicio',
            'estado',
            'fecha_registro',
        ]
    
class RepuestoMantenimientoFilter(django_filters.FilterSet):

    class Meta:
        model = RepuestoMantenimiento
        fields = [
            'mantenimiento',
            'repuesto',
        ]