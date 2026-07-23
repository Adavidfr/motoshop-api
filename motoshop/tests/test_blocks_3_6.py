from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from motoshop.apps import ROLES
from motoshop.models import CarritoCompras, ItemCarrito, Pedido
from motoshop.models.categoria_moto import CategoriaMoto
from motoshop.models.marca import Marca
from motoshop.models.moto import Moto
from motoshop.models.movimiento_inventario import MovimientoInventario
from motoshop.models.repuesto import Repuesto


class Block3VendedorRemovalTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.staff = User.objects.create_user(
            username='staff_inv', email='staff_inv@example.com',
            password='password123', is_staff=True,
        )
        self.client_user = User.objects.create_user(
            username='client_inv', email='client_inv@example.com',
            password='password123', is_staff=False,
        )
        Group.objects.get_or_create(name='vendedor')
        self.client_user.groups.add(Group.objects.get(name='vendedor'))
        self.repuesto = Repuesto.objects.create(
            nombre='Tornillo', sku='TOR-INV', costo=Decimal('1.00'),
            precio_venta=Decimal('2.00'), stock=5, estado='disponible',
        )

    def test_roles_constant_excludes_vendedor(self):
        self.assertNotIn('vendedor', ROLES)

    def test_vendedor_group_user_cannot_create_inventory_movement(self):
        self.client.force_authenticate(user=self.client_user)
        response = self.client.post('/api/movimientos-inventario/', {
            'tipo_movimiento': 'entrada',
            'cantidad': 1,
            'descripcion': 'test',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(MovimientoInventario.objects.count(), 0)

    def test_staff_can_create_inventory_movement(self):
        self.client.force_authenticate(user=self.staff)
        response = self.client.post('/api/movimientos-inventario/', {
            'tipo_movimiento': 'entrada',
            'cantidad': 1,
            'descripcion': 'test',
            'repuesto': self.repuesto.id_repuesto,
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class CartOrderOwnershipTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.marca = Marca.objects.create(nombre='Honda', estado=True)
        self.categoria = CategoriaMoto.objects.create(nombre='Naked', estado=True)
        self.moto = Moto.objects.create(
            categoria=self.categoria,
            marca=self.marca,
            modelo='CB500',
            anio=2024,
            cilindraje=500,
            color='Rojo',
            precio=Decimal('8000.00'),
            stock=5,
            estado='disponible',
        )
        self.staff = User.objects.create_user(
            username='staff_cart', email='staff_cart@example.com',
            password='password123', is_staff=True,
        )
        self.client_a = User.objects.create_user(
            username='client_a', email='client_a@example.com',
            password='password123', is_staff=False,
        )
        self.client_b = User.objects.create_user(
            username='client_b', email='client_b@example.com',
            password='password123', is_staff=False,
        )
        self.cart_a = CarritoCompras.objects.create(
            id_usuario_cliente=self.client_a, estado='activo',
        )
        self.cart_b = CarritoCompras.objects.create(
            id_usuario_cliente=self.client_b, estado='activo',
        )

    def test_staff_can_list_all_carts_but_cannot_create(self):
        self.client.force_authenticate(user=self.staff)
        listing = self.client.get('/api/carritos/')
        self.assertEqual(listing.status_code, status.HTTP_200_OK)
        self.assertEqual(listing.data['count'], 2)

        create = self.client.post('/api/carritos/', {'estado': 'activo'}, format='json')
        self.assertEqual(create.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_cannot_add_item_to_cart(self):
        self.client.force_authenticate(user=self.staff)
        response = self.client.post(
            f'/api/carritos/{self.cart_a.id_carrito}/add-item/',
            {'id_moto': self.moto.id_moto, 'cantidad': 1},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_client_cannot_use_foreign_cart(self):
        self.client.force_authenticate(user=self.client_a)
        response = self.client.post(
            f'/api/carritos/{self.cart_b.id_carrito}/add-item/',
            {'id_moto': self.moto.id_moto, 'cantidad': 1},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_staff_cannot_create_pedido(self):
        ItemCarrito.objects.create(
            id_carrito=self.cart_a,
            id_moto=self.moto.id_moto,
            cantidad=1,
            precio_unitario=self.moto.precio,
        )
        self.client.force_authenticate(user=self.staff)
        response = self.client.post('/api/pedidos/', {
            'id_carrito': self.cart_a.id_carrito,
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_client_cannot_create_pedido_from_foreign_cart(self):
        self.client.force_authenticate(user=self.client_a)
        response = self.client.post('/api/pedidos/', {
            'id_carrito': self.cart_b.id_carrito,
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PriceFromDatabaseTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='buyer_price', email='buyer_price@example.com',
            password='password123', is_staff=False,
        )
        self.marca = Marca.objects.create(nombre='Kawasaki', estado=True)
        self.categoria = CategoriaMoto.objects.create(nombre='Sport', estado=True)
        self.moto = Moto.objects.create(
            categoria=self.categoria,
            marca=self.marca,
            modelo='Ninja',
            anio=2024,
            cilindraje=400,
            color='Verde',
            precio=Decimal('9500.00'),
            stock=3,
            estado='disponible',
        )
        self.repuesto = Repuesto.objects.create(
            nombre='Filtro aceite',
            sku='FIL-001',
            costo=Decimal('5.00'),
            precio_venta=Decimal('12.50'),
            stock=10,
            estado='activo',
        )
        self.cart = CarritoCompras.objects.create(
            id_usuario_cliente=self.user, estado='activo',
        )
        self.client.force_authenticate(user=self.user)

    def test_add_item_uses_database_price_for_moto(self):
        response = self.client.post(
            f'/api/carritos/{self.cart.id_carrito}/add-item/',
            {
                'id_moto': self.moto.id_moto,
                'cantidad': 1,
                'precio_unitario': '1.00',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('precio_unitario', response.data)

        response = self.client.post(
            f'/api/carritos/{self.cart.id_carrito}/add-item/',
            {'id_moto': self.moto.id_moto, 'cantidad': 1},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item = ItemCarrito.objects.get(id_carrito=self.cart)
        self.assertEqual(item.precio_unitario, Decimal('9500.00'))

    def test_add_item_uses_database_price_for_repuesto(self):
        response = self.client.post(
            f'/api/carritos/{self.cart.id_carrito}/add-item/',
            {'id_repuesto': self.repuesto.id_repuesto, 'cantidad': 2},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item = ItemCarrito.objects.get(id_carrito=self.cart, id_repuesto=self.repuesto.id_repuesto)
        self.assertEqual(item.precio_unitario, Decimal('12.50'))


class StockValidationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='buyer_stock', email='buyer_stock@example.com',
            password='password123', is_staff=False,
        )
        self.marca = Marca.objects.create(nombre='Suzuki', estado=True)
        self.categoria = CategoriaMoto.objects.create(nombre='Touring', estado=True)
        self.moto = Moto.objects.create(
            categoria=self.categoria,
            marca=self.marca,
            modelo='V-Strom',
            anio=2023,
            cilindraje=650,
            color='Negro',
            precio=Decimal('11000.00'),
            stock=2,
            estado='disponible',
        )
        self.cart = CarritoCompras.objects.create(
            id_usuario_cliente=self.user, estado='activo',
        )
        self.client.force_authenticate(user=self.user)

    def test_add_item_rejects_quantity_above_stock(self):
        response = self.client.post(
            f'/api/carritos/{self.cart.id_carrito}/add-item/',
            {'id_moto': self.moto.id_moto, 'cantidad': 3},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Stock insuficiente', str(response.data))

    def test_confirm_pedido_revalidates_stock(self):
        ItemCarrito.objects.create(
            id_carrito=self.cart,
            id_moto=self.moto.id_moto,
            cantidad=2,
            precio_unitario=self.moto.precio,
        )
        pedido = Pedido.objects.create(
            id_usuario_cliente=self.user,
            id_carrito=self.cart,
            estado='pending',
            total=Decimal('22000.00'),
        )
        self.moto.stock = 1
        self.moto.save(update_fields=['stock'])

        response = self.client.post(f'/api/pedidos/{pedido.id_pedido}/confirm/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Stock insuficiente', response.data['error'])
