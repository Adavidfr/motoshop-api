"""
Pruebas de concurrencia — requieren PostgreSQL real (select_for_update).

Ejecutar:
  python manage.py test motoshop.tests.test_concurrency_postgres --settings=config.settings_test_postgres
"""

import threading
from decimal import Decimal

from django.contrib.auth.models import User
from django.db import IntegrityError, connection, connections, close_old_connections
from django.test import TransactionTestCase, tag
from rest_framework.exceptions import ValidationError

from motoshop.models import (
    CarritoCompras,
    Compra,
    ItemCarrito,
    Mantenimiento,
    MovimientoInventario,
    Pedido,
    Proveedor,
    Venta,
)
from motoshop.models.categoria_moto import CategoriaMoto
from motoshop.models.marca import Marca
from motoshop.models.moto import Moto
from motoshop.models.repuesto import Repuesto
from motoshop.models.servicio import Servicio
from motoshop.services import (
    CompraService,
    MantenimientoService,
    PedidoService,
    VentaService,
)
from motoshop.services.exceptions import BusinessError


@tag('postgres')
class ConcurrencyPostgresTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        if connection.vendor != 'postgresql':
            self.skipTest('Requiere PostgreSQL (--settings=config.settings_test_postgres)')

        self.marca = Marca.objects.create(nombre='HondaPG', estado=True)
        self.categoria = CategoriaMoto.objects.create(nombre='PG', estado=True)
        self.moto = Moto.objects.create(
            categoria=self.categoria, marca=self.marca, modelo='Unica',
            anio=2024, cilindraje=125, color='Rojo',
            precio=Decimal('3000.00'), stock=1, estado='disponible',
        )
        self.admin = User.objects.create_user(
            username='admin_pg', email='pg@t.com', password='x', is_staff=True,
        )
        self.cliente = User.objects.create_user(
            username='cli_pg', email='cpg@t.com', password='x', is_staff=False,
        )
        self.proveedor = Proveedor.objects.create(nombre='ProvPG', estado=True)
        self.repuesto = Repuesto.objects.create(
            nombre='RPG', sku='RPG-1', costo=Decimal('1'),
            precio_venta=Decimal('2'), stock=10, estado='disponible',
        )
        self.servicio = Servicio.objects.create(
            nombre='SrvPG', precio_base=Decimal('10'), tiempo_estimado_minutos=30, estado=True,
        )

    def _pedido_confirmado_con_moto(self, suffix='a'):
        user = User.objects.create_user(
            username=f'u_{suffix}', email=f'{suffix}@t.com', password='x', is_staff=False,
        )
        carrito = CarritoCompras.objects.create(id_usuario_cliente=user, estado='activo')
        ItemCarrito.objects.create(
            id_carrito=carrito, id_moto=self.moto.id_moto, cantidad=1,
            precio_unitario=self.moto.precio,
        )
        pedido = PedidoService.crear_desde_carrito(user, carrito)
        PedidoService.confirmar(pedido, user)
        return pedido

    def test_dos_ventas_concurrentes_stock_uno(self):
        pedido_a = self._pedido_confirmado_con_moto('a')
        pedido_b = self._pedido_confirmado_con_moto('b')
        resultados = {
            'ok': 0,
            'error': 0,
            'inesperado': 0,
            'errores': [],
            'errores_inesperados': [],
        }
        lock = threading.Lock()

        def intentar(pedido_id):
            close_old_connections()
            try:
                VentaService.crear_venta_desde_pedido(pedido_id, self.admin)
                with lock:
                    resultados['ok'] += 1
            except BusinessError as exc:
                with lock:
                    resultados['error'] += 1
                    resultados['errores'].append(str(exc))
            except ValidationError as exc:
                with lock:
                    resultados['error'] += 1
                    resultados['errores'].append(str(exc.detail))
            except IntegrityError as exc:
                with lock:
                    resultados['error'] += 1
                    resultados['errores'].append(str(exc))
            except Exception as exc:
                with lock:
                    resultados['inesperado'] += 1
                    resultados['errores_inesperados'].append(
                        f'{type(exc).__name__}: {exc}'
                    )
            finally:
                close_old_connections()
                connections.close_all()

        t1 = threading.Thread(target=intentar, args=(pedido_a.pk,))
        t2 = threading.Thread(target=intentar, args=(pedido_b.pk,))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        self.assertEqual(resultados['ok'], 1, msg=f"errores={resultados['errores']}")
        self.assertEqual(resultados['error'], 1, msg=f"inesperados={resultados['errores_inesperados']}")
        self.assertEqual(resultados['inesperado'], 0, msg=resultados['errores_inesperados'])

        self.assertEqual(
            Venta.objects.filter(id_pedido__in=[pedido_a.pk, pedido_b.pk]).count(),
            1,
        )
        self.assertEqual(Venta.objects.count(), 1)

        self.moto.refresh_from_db()
        self.assertEqual(self.moto.stock, 0)
        self.assertEqual(self.moto.estado, 'vendida')
        self.assertGreaterEqual(self.moto.stock, 0)

        movimientos_venta = MovimientoInventario.objects.filter(
            moto=self.moto,
            tipo_movimiento='venta',
        )
        self.assertEqual(movimientos_venta.count(), 1)
        self.assertEqual(movimientos_venta.first().cantidad, -1)

    def test_compra_recibida_concurrente_idempotente(self):
        compra = Compra.objects.create(
            proveedor=self.proveedor, repuesto=self.repuesto,
            cantidad=3, precio_unitario=Decimal('5'), subtotal=Decimal('15'),
            estado='Pendiente',
        )
        stock_antes = self.repuesto.stock

        def recibir():
            from django.db import close_old_connections
            close_old_connections()
            try:
                c = Compra.objects.get(pk=compra.pk)
                CompraService.cambiar_estado(c, 'Recibida', self.admin)
            finally:
                connections.close_all()

        threads = [threading.Thread(target=recibir) for _ in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        compra.refresh_from_db()
        self.repuesto.refresh_from_db()
        self.assertTrue(compra.stock_aplicado)
        self.assertEqual(self.repuesto.stock, stock_antes + 3)

    def test_mantenimiento_finalizar_dos_veces(self):
        mant = Mantenimiento.objects.create(
            moto=self.moto, usuario_cliente=self.cliente, servicio=self.servicio,
            kilometraje_actual=100, costo_final=Decimal('10'), estado='En proceso',
        )
        MantenimientoService.cambiar_estado(mant, 'Finalizado', self.admin)
        mant.refresh_from_db()
        with self.assertRaises(BusinessError):
            MantenimientoService.cambiar_estado(mant, 'Finalizado', self.admin)
