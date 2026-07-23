"""Pruebas del flujo comercial integrado (services + transacciones)."""

from decimal import Decimal
from io import BytesIO

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from motoshop.models import (
    CarritoCompras,
    Compra,
    ItemCarrito,
    MovimientoInventario,
    Notificacion,
    Pedido,
    Proveedor,
    Venta,
)
from motoshop.models.categoria_moto import CategoriaMoto
from motoshop.models.historial_estado_venta import HistorialEstadoVenta
from motoshop.models.marca import Marca
from motoshop.models.moto import Moto
from motoshop.models.repuesto import Repuesto
from motoshop.services import (
    CarritoService,
    CompraService,
    FinanciamientoService,
    PedidoService,
    VentaService,
)


@override_settings(
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
)
class FlujoComercialTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.marca = Marca.objects.create(nombre='Yamaha', estado=True)
        self.categoria = CategoriaMoto.objects.create(nombre='Sport', estado=True)
        self.moto = Moto.objects.create(
            categoria=self.categoria,
            marca=self.marca,
            modelo='R3',
            anio=2024,
            cilindraje=320,
            color='Azul',
            precio=Decimal('5500.00'),
            stock=3,
            estado='disponible',
        )
        self.repuesto = Repuesto.objects.create(
            nombre='Filtro aceite',
            descripcion='Filtro',
            sku='FIL-001',
            costo=Decimal('5.00'),
            precio_venta=Decimal('12.00'),
            stock=10,
            estado='disponible',
        )
        self.cliente = User.objects.create_user(
            username='cliente_fc', email='fc@example.com',
            password='pass123', is_staff=False,
        )
        self.admin = User.objects.create_user(
            username='admin_fc', email='admin_fc@example.com',
            password='pass123', is_staff=True,
        )
        self.otro = User.objects.create_user(
            username='otro_fc', email='otro@example.com',
            password='pass123', is_staff=False,
        )
        self.proveedor = Proveedor.objects.create(
            nombre='Proveedor FC', contacto='999', correo='p@fc.com', estado=True,
        )

    def _carrito_con_moto(self, usuario=None):
        user = usuario or self.cliente
        carrito, _ = CarritoService.obtener_o_crear_activo(user)
        CarritoService.agregar_item(carrito, user, id_moto=self.moto.id_moto, cantidad=1)
        return carrito

    def test_precio_desde_bd_en_carrito(self):
        carrito = self._carrito_con_moto()
        item = carrito.items.first()
        self.assertEqual(item.precio_unitario, self.moto.precio)
        self.assertEqual(item.subtotal, self.moto.precio)

    def test_stock_insuficiente_carrito(self):
        carrito, _ = CarritoService.obtener_o_crear_activo(self.cliente)
        from motoshop.services.exceptions import BusinessError
        with self.assertRaises(BusinessError):
            CarritoService.agregar_item(
                carrito, self.cliente, id_moto=self.moto.id_moto, cantidad=100,
            )

    def test_carrito_ajeno(self):
        carrito = self._carrito_con_moto()
        from motoshop.services.exceptions import BusinessError
        with self.assertRaises(BusinessError):
            CarritoService.agregar_item(
                carrito, self.otro, id_moto=self.moto.id_moto, cantidad=1,
            )

    def test_carrito_procesado_inmutable(self):
        carrito = self._carrito_con_moto()
        pedido = PedidoService.crear_desde_carrito(self.cliente, carrito)
        self.assertEqual(pedido.estado, 'pending')
        carrito.refresh_from_db()
        from motoshop.services.exceptions import BusinessError
        with self.assertRaises(BusinessError):
            CarritoService.agregar_item(
                carrito, self.cliente, id_repuesto=self.repuesto.id_repuesto, cantidad=1,
            )

    def test_pedido_duplicado_mismo_carrito(self):
        carrito = self._carrito_con_moto()
        PedidoService.crear_desde_carrito(self.cliente, carrito)
        carrito2 = CarritoCompras.objects.get(pk=carrito.pk)
        from motoshop.services.exceptions import BusinessError
        with self.assertRaises(BusinessError):
            PedidoService.crear_desde_carrito(self.cliente, carrito2)

    def test_venta_solo_desde_pedido_confirmado(self):
        carrito = self._carrito_con_moto()
        pedido = PedidoService.crear_desde_carrito(self.cliente, carrito)
        from motoshop.services.exceptions import BusinessError
        with self.assertRaises(BusinessError):
            VentaService.crear_venta_desde_pedido(pedido.pk, self.admin)

    def test_venta_descuenta_stock_y_crea_movimientos(self):
        carrito = self._carrito_con_moto()
        pedido = PedidoService.crear_desde_carrito(self.cliente, carrito)
        PedidoService.confirmar(pedido, self.cliente)
        stock_antes = self.moto.stock
        venta = VentaService.crear_venta_desde_pedido(pedido.pk, self.admin)
        pedido.refresh_from_db()
        self.assertEqual(pedido.estado, 'confirmed')
        self.moto.refresh_from_db()
        self.assertEqual(self.moto.stock, stock_antes - 1)
        self.assertEqual(venta.total_venta, self.moto.precio)
        self.assertTrue(MovimientoInventario.objects.filter(tipo_movimiento='venta').exists())
        self.assertTrue(HistorialEstadoVenta.objects.filter(id_venta=venta).exists())
        self.assertTrue(Notificacion.objects.filter(id_usuario=self.cliente).exists())

    def test_una_sola_venta_por_pedido(self):
        carrito = self._carrito_con_moto()
        pedido = PedidoService.crear_desde_carrito(self.cliente, carrito)
        PedidoService.confirmar(pedido, self.cliente)
        VentaService.crear_venta_desde_pedido(pedido.pk, self.admin)
        from motoshop.services.exceptions import BusinessError
        with self.assertRaises(BusinessError):
            VentaService.crear_venta_desde_pedido(pedido.pk, self.admin)

    def test_compra_recibida_aumenta_stock_una_vez(self):
        compra = Compra.objects.create(
            proveedor=self.proveedor,
            repuesto=self.repuesto,
            cantidad=5,
            precio_unitario=Decimal('8.00'),
            subtotal=Decimal('40.00'),
            estado='Pendiente',
        )
        stock_antes = self.repuesto.stock
        CompraService.cambiar_estado(compra, 'Recibida', self.admin)
        self.repuesto.refresh_from_db()
        compra.refresh_from_db()
        self.assertEqual(self.repuesto.stock, stock_antes + 5)
        self.assertTrue(compra.stock_aplicado)
        mov_count = MovimientoInventario.objects.filter(tipo_movimiento='compra').count()
        CompraService.cambiar_estado(compra, 'Recibida', self.admin)
        self.repuesto.refresh_from_db()
        self.assertEqual(
            MovimientoInventario.objects.filter(tipo_movimiento='compra').count(),
            mov_count,
        )

    def test_api_venta_rechaza_total_frontend(self):
        carrito = self._carrito_con_moto()
        pedido = PedidoService.crear_desde_carrito(self.cliente, carrito)
        PedidoService.confirmar(pedido, self.cliente)
        self.client.force_authenticate(user=self.admin)
        response = self.client.post('/api/ventas/', {
            'id_pedido': pedido.pk,
            'total_venta': '99999.00',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_pago_superior_al_saldo(self):
        carrito = self._carrito_con_moto()
        pedido = PedidoService.crear_desde_carrito(self.cliente, carrito)
        PedidoService.confirmar(pedido, self.cliente)
        venta = VentaService.crear_venta_desde_pedido(pedido.pk, self.admin)
        self.client.force_authenticate(user=self.admin)
        response = self.client.post('/api/pagos/', {
            'id_venta': venta.pk,
            'monto': str(venta.total_venta + 100),
            'metodo_pago': 'efectivo',
            'tipo_pago': 'contado',
            'estado': 'completado',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_pago_con_financiamiento_via_api(self):
        carrito = self._carrito_con_moto()
        pedido = PedidoService.crear_desde_carrito(self.cliente, carrito)
        PedidoService.confirmar(pedido, self.cliente)
        venta = VentaService.crear_venta_desde_pedido(pedido.pk, self.admin)
        financiamiento = FinanciamientoService.crear(
            venta=venta,
            entidad_financiera='Banco Test',
            monto_financiado=venta.total_venta,
            tasa_interes=Decimal('0'),
            plazo_meses=12,
            entrada=Decimal('0'),
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.post('/api/pagos/', {
            'id_venta': venta.pk,
            'id_financiamiento': financiamiento.pk,
            'monto': '500.00',
            'metodo_pago': 'transferencia',
            'tipo_pago': 'cuota',
            'estado': 'completado',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['id_financiamiento'], financiamiento.pk)
        self.assertEqual(response.data['tipo_pago'], 'cuota')
        financiamiento.refresh_from_db()
        self.assertEqual(financiamiento.saldo_pendiente, venta.total_venta - Decimal('500.00'))

    def test_historial_no_editable_via_api(self):
        carrito = self._carrito_con_moto()
        pedido = PedidoService.crear_desde_carrito(self.cliente, carrito)
        PedidoService.confirmar(pedido, self.cliente)
        VentaService.crear_venta_desde_pedido(pedido.pk, self.admin)
        self.client.force_authenticate(user=self.admin)
        response = self.client.post('/api/historial-estado-venta/', {
            'id_venta': 1,
            'estado_anterior': 'x',
            'estado_nuevo': 'y',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_documento_pdf_y_descarga(self):
        carrito = self._carrito_con_moto()
        pedido = PedidoService.crear_desde_carrito(self.cliente, carrito)
        PedidoService.confirmar(pedido, self.cliente)
        venta = VentaService.crear_venta_desde_pedido(pedido.pk, self.admin)
        pdf = SimpleUploadedFile('contrato.pdf', b'%PDF-1.4 test', content_type='application/pdf')
        self.client.force_authenticate(user=self.admin)
        create_resp = self.client.post('/api/documentos-venta/', {
            'id_venta': venta.pk,
            'tipo_documento': 'contrato',
            'archivo': pdf,
        }, format='multipart')
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED)
        doc_id = create_resp.data['id_documento']
        self.client.force_authenticate(user=self.cliente)
        dl = self.client.get(f'/api/documentos-venta/{doc_id}/archivo/')
        self.assertEqual(dl.status_code, status.HTTP_200_OK)
        self.client.force_authenticate(user=self.otro)
        dl_otro = self.client.get(f'/api/documentos-venta/{doc_id}/archivo/')
        self.assertEqual(dl_otro.status_code, status.HTTP_404_NOT_FOUND)

    def test_resumen_venta_endpoint(self):
        carrito = self._carrito_con_moto()
        pedido = PedidoService.crear_desde_carrito(self.cliente, carrito)
        PedidoService.confirmar(pedido, self.cliente)
        venta = VentaService.crear_venta_desde_pedido(pedido.pk, self.admin)
        self.client.force_authenticate(user=self.cliente)
        response = self.client.get(f'/api/ventas/{venta.pk}/resumen/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_pagado', response.data)
        self.assertIn('saldo_pendiente', response.data)
