"""Pruebas de ajustes finales pre-migración PostgreSQL."""

from decimal import Decimal

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from motoshop.models import (
    CarritoCompras,
    Devolucion,
    Factura,
    ItemCarrito,
    Pago,
    Pedido,
    Venta,
)
from motoshop.models.categoria_moto import CategoriaMoto
from motoshop.models.marca import Marca
from motoshop.models.moto import Moto
from motoshop.models.movimiento_inventario import MovimientoInventario
from motoshop.services import DevolucionService, FacturaService, PedidoService, VentaService
from motoshop.services.exceptions import BusinessError
from motoshop.utils.facturacion import descomponer_total_con_iva


@override_settings(
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    MOTOSHOP_IVA_RATE=Decimal('0.15'),
)
class AjustesFinalesTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.marca = Marca.objects.create(nombre='KTM', estado=True)
        self.categoria = CategoriaMoto.objects.create(nombre='Enduro', estado=True)
        self.moto = Moto.objects.create(
            categoria=self.categoria, marca=self.marca, modelo='390',
            anio=2024, cilindraje=390, color='Naranja',
            precio=Decimal('7000.00'), stock=2, estado='disponible',
        )
        self.cliente = User.objects.create_user(
            username='cli_aj', email='aj@t.com', password='x', is_staff=False,
        )
        self.admin = User.objects.create_user(
            username='adm_aj', email='adm@t.com', password='x', is_staff=True,
        )

    def _venta_confirmada(self):
        carrito = CarritoCompras.objects.create(
            id_usuario_cliente=self.cliente, estado='procesado',
        )
        ItemCarrito.objects.create(
            id_carrito=carrito, id_moto=self.moto.id_moto, cantidad=1,
            precio_unitario=self.moto.precio,
        )
        pedido = Pedido.objects.create(
            id_usuario_cliente=self.cliente, id_carrito=carrito,
            estado='confirmed', total=self.moto.precio,
        )
        venta = VentaService.crear_venta_desde_pedido(pedido.pk, self.admin)
        pedido.refresh_from_db()
        return pedido, venta

    def test_venta_mantiene_pedido_en_confirmed(self):
        pedido, _ = self._venta_confirmada()
        self.assertEqual(pedido.estado, 'confirmed')

    def test_admin_cambia_pedido_a_shipped_explicitamente(self):
        pedido, _ = self._venta_confirmada()
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            f'/api/pedidos/{pedido.id_pedido}/update-status/',
            {'estado': 'shipped'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pedido.refresh_from_db()
        self.assertEqual(pedido.estado, 'shipped')

    @override_settings(MOTOSHOP_IVA_RATE=Decimal('0.15'))
    def test_iva_configurable_decimal_sin_doble_aplicacion(self):
        pedido, venta = self._venta_confirmada()
        pago = Pago.objects.create(
            id_venta=venta, monto=venta.total_venta, metodo_pago='efectivo',
            estado='completado', tipo_pago='contado', procesado_por=self.admin,
        )
        factura = FacturaService.emitir(pago, 'FAC-IVA-001')
        subtotal, iva, total = descomponer_total_con_iva(pago.monto)
        self.assertEqual(factura.subtotal, subtotal)
        self.assertEqual(factura.iva, iva)
        self.assertEqual(factura.total, pago.monto)
        self.assertEqual(subtotal + iva, total)

    @override_settings(MOTOSHOP_IVA_RATE=Decimal('0.10'))
    def test_iva_distinta_por_settings(self):
        _, venta = self._venta_confirmada()
        pago = Pago.objects.create(
            id_venta=venta, monto=Decimal('7000.00'), metodo_pago='efectivo',
            estado='completado', tipo_pago='contado', procesado_por=self.admin,
        )
        factura = FacturaService.emitir(pago, 'FAC-IVA-002')
        subtotal, iva, _ = descomponer_total_con_iva(Decimal('7000.00'))
        self.assertEqual(factura.subtotal, subtotal)
        self.assertEqual(factura.iva, iva)

    def test_devolucion_sin_pagos_reembolso_cero(self):
        pedido, venta = self._venta_confirmada()
        dev = DevolucionService.solicitar(
            venta, self.cliente, 'Defecto', Decimal('0'),
        )
        dev = DevolucionService.cambiar_estado(dev, 'aprobada', self.admin)
        self.assertEqual(dev.monto_reembolso_aplicado, Decimal('0'))
        self.assertTrue(dev.stock_reintegrado)
        self.assertEqual(Pago.objects.filter(id_venta=venta, tipo_pago='reembolso').count(), 0)

    def test_devolucion_con_pago_parcial(self):
        pedido, venta = self._venta_confirmada()
        Pago.objects.create(
            id_venta=venta, monto=Decimal('2000.00'), metodo_pago='efectivo',
            estado='completado', tipo_pago='contado', procesado_por=self.admin,
        )
        dev = DevolucionService.solicitar(
            venta, self.cliente, 'Parcial', Decimal('1500.00'),
        )
        dev = DevolucionService.cambiar_estado(dev, 'aprobada', self.admin)
        self.assertEqual(dev.monto_reembolso_aplicado, Decimal('1500.00'))

    def test_devolucion_sin_pagos_rechaza_monto_positivo(self):
        _, venta = self._venta_confirmada()
        with self.assertRaises(BusinessError):
            DevolucionService.solicitar(
                venta, self.cliente, 'Sin pago', Decimal('100.00'),
            )

    def test_reembolso_superior_a_pagado_rechazado(self):
        _, venta = self._venta_confirmada()
        Pago.objects.create(
            id_venta=venta, monto=Decimal('500.00'), metodo_pago='efectivo',
            estado='completado', tipo_pago='contado', procesado_por=self.admin,
        )
        with self.assertRaises(BusinessError):
            DevolucionService.solicitar(
                venta, self.cliente, 'Exceso', Decimal('600.00'),
            )

    def test_aprobacion_duplicada_rechazada(self):
        _, venta = self._venta_confirmada()
        dev = DevolucionService.solicitar(venta, self.cliente, 'Física', Decimal('0'))
        DevolucionService.cambiar_estado(dev, 'aprobada', self.admin)
        dev.refresh_from_db()
        with self.assertRaises(BusinessError):
            DevolucionService.cambiar_estado(dev, 'aprobada', self.admin)

    def test_documento_rechaza_archivo_url_legacy_en_post(self):
        _, venta = self._venta_confirmada()
        self.client.force_authenticate(user=self.admin)
        pdf = SimpleUploadedFile('x.pdf', b'%PDF', content_type='application/pdf')
        response = self.client.post('/api/documentos-venta/', {
            'id_venta': venta.pk,
            'tipo_documento': 'contrato',
            'archivo': pdf,
            'archivo_url_legacy': 'http://evil.com/doc.pdf',
        }, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_documento_rechaza_archivo_url_en_post(self):
        _, venta = self._venta_confirmada()
        self.client.force_authenticate(user=self.admin)
        pdf = SimpleUploadedFile('x.pdf', b'%PDF', content_type='application/pdf')
        response = self.client.post('/api/documentos-venta/', {
            'id_venta': venta.pk,
            'tipo_documento': 'contrato',
            'archivo': pdf,
            'archivo_url': '/media/evil.pdf',
        }, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_numero_factura_autogenerado_formato(self):
        _, venta = self._venta_confirmada()
        pago = Pago.objects.create(
            id_venta=venta, monto=venta.total_venta, metodo_pago='efectivo',
            estado='completado', tipo_pago='contado', procesado_por=self.admin,
        )
        factura = FacturaService.emitir(pago)
        self.assertRegex(factura.numero_factura, r'^FAC-\d{4}-\d{6}$')

    def test_numero_factura_secuencial_por_anio(self):
        from django.utils import timezone

        year = timezone.now().year
        _, venta1 = self._venta_confirmada()
        pago1 = Pago.objects.create(
            id_venta=venta1, monto=venta1.total_venta, metodo_pago='efectivo',
            estado='completado', tipo_pago='contado', procesado_por=self.admin,
        )
        f1 = FacturaService.emitir(pago1)
        Factura.objects.filter(pk=f1.pk).update(numero_factura=f'FAC-{year}-000005')

        _, venta2 = self._venta_confirmada()
        pago2 = Pago.objects.create(
            id_venta=venta2, monto=venta2.total_venta, metodo_pago='efectivo',
            estado='completado', tipo_pago='contado', procesado_por=self.admin,
        )
        f2 = FacturaService.emitir(pago2)
        self.assertEqual(f2.numero_factura, f'FAC-{year}-000006')

    def test_api_emitir_factura_solo_id_pago(self):
        _, venta = self._venta_confirmada()
        pago = Pago.objects.create(
            id_venta=venta, monto=venta.total_venta, metodo_pago='efectivo',
            estado='completado', tipo_pago='contado', procesado_por=self.admin,
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.post('/api/facturas/', {
            'id_pago': pago.pk,
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertRegex(response.data['numero_factura'], r'^FAC-\d{4}-\d{6}$')
        self.assertEqual(response.data['id_pago'], pago.pk)
        self.assertEqual(response.data['id_venta'], venta.pk)

    def test_api_rechaza_numero_factura_manual(self):
        _, venta = self._venta_confirmada()
        pago = Pago.objects.create(
            id_venta=venta, monto=venta.total_venta, metodo_pago='efectivo',
            estado='completado', tipo_pago='contado', procesado_por=self.admin,
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.post('/api/facturas/', {
            'id_pago': pago.pk,
            'numero_factura': 'FAC-MANUAL-001',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('numero_factura', response.data)

    def test_factura_por_cada_pago_sin_factura_global(self):
        _, venta = self._venta_confirmada()
        pago1 = Pago.objects.create(
            id_venta=venta, monto=Decimal('2000.00'), metodo_pago='efectivo',
            estado='completado', tipo_pago='entrada', procesado_por=self.admin,
        )
        pago2 = Pago.objects.create(
            id_venta=venta, monto=Decimal('500.00'), metodo_pago='transferencia',
            estado='completado', tipo_pago='cuota', procesado_por=self.admin,
        )
        f1 = FacturaService.emitir(pago1)
        f2 = FacturaService.emitir(pago2)
        self.assertEqual(f1.total, Decimal('2000.00'))
        self.assertEqual(f2.total, Decimal('500.00'))
        self.assertEqual(
            Factura.objects.filter(id_pago__id_venta=venta).count(),
            2,
        )

    def test_pago_serializer_incluye_factura_resumen(self):
        _, venta = self._venta_confirmada()
        pago = Pago.objects.create(
            id_venta=venta, monto=Decimal('500.00'), metodo_pago='efectivo',
            estado='completado', tipo_pago='cuota', procesado_por=self.admin,
        )
        factura = FacturaService.emitir(pago, 'FAC-PAGO-RES-001')

        from motoshop.serializers.pago import PagoSerializer
        data = PagoSerializer(pago).data
        self.assertIsNotNone(data['factura'])
        self.assertEqual(data['factura']['id_factura'], factura.id_factura)
        self.assertEqual(data['factura']['numero_factura'], 'FAC-PAGO-RES-001')

    def test_pago_sin_factura_devuelve_null(self):
        _, venta = self._venta_confirmada()
        pago = Pago.objects.create(
            id_venta=venta, monto=Decimal('300.00'), metodo_pago='efectivo',
            estado='completado', tipo_pago='contado', procesado_por=self.admin,
        )
        from motoshop.serializers.pago import PagoSerializer
        data = PagoSerializer(pago).data
        self.assertIsNone(data['factura'])

    def test_rechaza_factura_duplicada_mismo_pago(self):
        _, venta = self._venta_confirmada()
        pago = Pago.objects.create(
            id_venta=venta, monto=Decimal('1000.00'), metodo_pago='efectivo',
            estado='completado', tipo_pago='contado', procesado_por=self.admin,
        )
        FacturaService.emitir(pago)
        with self.assertRaises(BusinessError):
            FacturaService.emitir(pago)

    def test_api_pago_list_incluye_factura(self):
        _, venta = self._venta_confirmada()
        pago = Pago.objects.create(
            id_venta=venta, monto=Decimal('750.00'), metodo_pago='tarjeta',
            estado='completado', tipo_pago='contado', procesado_por=self.admin,
        )
        FacturaService.emitir(pago)
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/pagos/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item = next(r for r in response.data['results'] if r['id_pago'] == pago.pk)
        self.assertIsNotNone(item['factura'])
        self.assertIn('numero_factura', item['factura'])

    def test_api_factura_pdf_descarga(self):
        _, venta = self._venta_confirmada()
        pago = Pago.objects.create(
            id_venta=venta, monto=Decimal('500.00'), metodo_pago='efectivo',
            estado='completado', tipo_pago='cuota', procesado_por=self.admin,
        )
        factura = FacturaService.emitir(pago)
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(f'/api/facturas/{factura.pk}/pdf/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertTrue(response.content.startswith(b'%PDF'))

    def test_api_factura_pdf_inline_para_impresion(self):
        _, venta = self._venta_confirmada()
        pago = Pago.objects.create(
            id_venta=venta, monto=Decimal('300.00'), metodo_pago='efectivo',
            estado='completado', tipo_pago='contado', procesado_por=self.admin,
        )
        factura = FacturaService.emitir(pago)
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(f'/api/facturas/{factura.pk}/pdf/?inline=1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('inline', response['Content-Disposition'])
