from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from motoshop.models import (
    CarritoCompras, Devolucion, Factura, Mantenimiento, Pedido, Pago, Venta,
)
from motoshop.models.categoria_moto import CategoriaMoto
from motoshop.models.marca import Marca
from motoshop.models.moto import Moto
from motoshop.models.servicio import Servicio


class Block7OrderSaleStatusTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.staff = User.objects.create_user(
            username='staff_status', email='staff_status@example.com',
            password='password123', is_staff=True,
        )
        self.client_user = User.objects.create_user(
            username='client_status', email='client_status@example.com',
            password='password123', is_staff=False,
        )
        self.cart = CarritoCompras.objects.create(
            id_usuario_cliente=self.client_user, estado='procesado',
        )
        self.pedido = Pedido.objects.create(
            id_usuario_cliente=self.client_user,
            id_carrito=self.cart,
            estado='pending',
            total=Decimal('1000.00'),
        )
        self.venta = Venta.objects.create(
            id_pedido=self.pedido,
            id_usuario_cliente=self.client_user,
            id_usuario_vendedor=self.staff,
            total_venta=Decimal('1000.00'),
            estado='pendiente',
        )

    def test_client_cannot_patch_pedido_estado(self):
        self.client.force_authenticate(user=self.client_user)
        response = self.client.patch(
            f'/api/pedidos/{self.pedido.id_pedido}/',
            {'estado': 'shipped'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_update_pedido_status(self):
        self.client.force_authenticate(user=self.staff)
        response = self.client.post(
            f'/api/pedidos/{self.pedido.id_pedido}/update-status/',
            {'estado': 'confirmed'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado, 'confirmed')
        response = self.client.post(
            f'/api/pedidos/{self.pedido.id_pedido}/update-status/',
            {'estado': 'shipped'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado, 'shipped')

    def test_client_cannot_patch_venta_estado(self):
        self.client.force_authenticate(user=self.client_user)
        response = self.client.patch(
            f'/api/ventas/{self.venta.id_venta}/',
            {'estado': 'completada'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_patch_venta_estado(self):
        self.client.force_authenticate(user=self.staff)
        response = self.client.patch(
            f'/api/ventas/{self.venta.id_venta}/',
            {'estado': 'completada'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.venta.refresh_from_db()
        self.assertEqual(self.venta.estado, 'completada')


class Block8OwnerFilteredReadTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.staff = User.objects.create_user(
            username='staff_owner', email='staff_owner@example.com',
            password='password123', is_staff=True,
        )
        self.client_a = User.objects.create_user(
            username='owner_a', email='owner_a@example.com',
            password='password123', is_staff=False,
        )
        self.client_b = User.objects.create_user(
            username='owner_b', email='owner_b@example.com',
            password='password123', is_staff=False,
        )
        self.marca = Marca.objects.create(nombre='BMW', estado=True)
        self.categoria = CategoriaMoto.objects.create(nombre='Touring', estado=True)
        self.moto = Moto.objects.create(
            categoria=self.categoria, marca=self.marca, modelo='GS',
            anio=2024, cilindraje=800, color='Negro',
            precio=Decimal('15000.00'), stock=1, estado='disponible',
        )
        self.servicio = Servicio.objects.create(
            nombre='Cambio de aceite',
            precio_base=Decimal('30.00'),
            tiempo_estimado_minutos=60,
            estado=True,
        )

        self.pedido_a = self._create_venta(self.client_a)
        self.venta_a = Venta.objects.get(id_pedido=self.pedido_a)
        self.pedido_b = self._create_venta(self.client_b)
        self.venta_b = Venta.objects.get(id_pedido=self.pedido_b)

        self.factura_a = Factura.objects.create(
            id_venta=self.venta_a,
            numero_factura='FAC-001',
            subtotal=Decimal('900.00'),
            iva=Decimal('100.00'),
            total=Decimal('1000.00'),
        )
        self.factura_b = Factura.objects.create(
            id_venta=self.venta_b,
            numero_factura='FAC-002',
            subtotal=Decimal('900.00'),
            iva=Decimal('100.00'),
            total=Decimal('1000.00'),
        )
        Mantenimiento.objects.create(
            moto=self.moto,
            usuario_cliente=self.client_a,
            servicio=self.servicio,
            kilometraje_actual=1000,
            costo_final=Decimal('30.00'),
            estado='Pendiente',
        )
        Mantenimiento.objects.create(
            moto=self.moto,
            usuario_cliente=self.client_b,
            servicio=self.servicio,
            kilometraje_actual=2000,
            costo_final=Decimal('30.00'),
            estado='Pendiente',
        )

    def _create_venta(self, user):
        cart = CarritoCompras.objects.create(id_usuario_cliente=user, estado='procesado')
        pedido = Pedido.objects.create(
            id_usuario_cliente=user,
            id_carrito=cart,
            estado='confirmed',
            total=Decimal('1000.00'),
        )
        Venta.objects.create(
            id_pedido=pedido,
            id_usuario_cliente=user,
            id_usuario_vendedor=self.staff,
            total_venta=Decimal('1000.00'),
            estado='completada',
        )
        return pedido

    def test_client_sees_only_own_facturas(self):
        self.client.force_authenticate(user=self.client_a)
        response = self.client.get('/api/facturas/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item['id_factura'] for item in response.data['results']]
        self.assertEqual(ids, [self.factura_a.id_factura])

    def test_client_cannot_see_foreign_factura_detail(self):
        self.client.force_authenticate(user=self.client_a)
        response = self.client.get(f'/api/facturas/{self.factura_b.id_factura}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_client_can_request_devolucion_on_own_venta(self):
        Pago.objects.create(
            id_venta=self.venta_a,
            monto=Decimal('100.00'),
            metodo_pago='efectivo',
            estado='completado',
            tipo_pago='contado',
            procesado_por=self.staff,
        )
        self.client.force_authenticate(user=self.client_a)
        response = self.client.post('/api/devoluciones/', {
            'id_venta': self.venta_a.id_venta,
            'motivo': 'Producto defectuoso',
            'monto_devolucion': '100.00',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_client_cannot_request_devolucion_on_foreign_venta(self):
        self.client.force_authenticate(user=self.client_a)
        response = self.client.post('/api/devoluciones/', {
            'id_venta': self.venta_b.id_venta,
            'motivo': 'Producto defectuoso',
            'monto_devolucion': '100.00',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Devolucion.objects.filter(id_venta=self.venta_b).exists())

    def test_client_sees_only_own_mantenimientos(self):
        self.client.force_authenticate(user=self.client_a)
        response = self.client.get('/api/mantenimientos/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(
            response.data['results'][0]['usuario_cliente'],
            self.client_a.id,
        )

    def test_client_cannot_create_pago(self):
        self.client.force_authenticate(user=self.client_a)
        response = self.client.post('/api/pagos/', {
            'id_venta': self.venta_a.id_venta,
            'monto': '100.00',
            'metodo_pago': 'efectivo',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class Block9ProcesadoPorTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.staff = User.objects.create_user(
            username='admin_proc', email='admin_proc@example.com',
            password='password123', is_staff=True,
        )
        self.client_user = User.objects.create_user(
            username='client_proc', email='client_proc@example.com',
            password='password123', is_staff=False,
        )
        cart = CarritoCompras.objects.create(
            id_usuario_cliente=self.client_user, estado='procesado',
        )
        pedido = Pedido.objects.create(
            id_usuario_cliente=self.client_user,
            id_carrito=cart,
            estado='confirmed',
            total=Decimal('500.00'),
        )
        self.venta = Venta.objects.create(
            id_pedido=pedido,
            id_usuario_cliente=self.client_user,
            id_usuario_vendedor=self.staff,
            total_venta=Decimal('500.00'),
            estado='completada',
        )

    def test_venta_includes_procesado_por_alias(self):
        self.client.force_authenticate(user=self.client_user)
        response = self.client.get(f'/api/ventas/{self.venta.id_venta}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id_usuario_vendedor'], self.staff.id)
        self.assertEqual(response.data['username_vendedor'], self.staff.username)
        self.assertEqual(response.data['procesado_por'], {
            'id': self.staff.id,
            'username': self.staff.username,
        })
