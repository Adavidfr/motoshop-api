"""
Verificación integrada del flujo comercial sobre la base configurada (PostgreSQL local).

Uso:
  set SEED_DEV_PASSWORD=...
  python manage.py verify_local_flow
"""

from decimal import Decimal
from io import BytesIO

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand
from decouple import config
from rest_framework import status
from rest_framework.test import APIClient

from motoshop.models import (
    CarritoCompras,
    HistorialEstadoVenta,
    Mantenimiento,
    MovimientoInventario,
    Notificacion,
    Pedido,
    RepuestoMantenimiento,
    Venta,
)
from motoshop.models.moto import Moto
from motoshop.services import (
    CarritoService,
    DevolucionService,
    FacturaService,
    FinanciamientoService,
    MantenimientoService,
    PagoService,
    PedidoService,
    VentaService,
)
from motoshop.services.exceptions import BusinessError
from motoshop.utils.facturacion import descomponer_total_con_iva


class Command(BaseCommand):
    help = 'Verifica flujo comercial completo y endpoints clave en la BD local.'

    def handle(self, *args, **options):
        password = config('SEED_DEV_PASSWORD', default='')
        admin_user = config('SEED_ADMIN_USERNAME', default='admin_dev')
        client_user = config('SEED_CLIENT_USERNAME', default='cliente_dev')

        if not password:
            self.stderr.write(
                'Defina SEED_DEV_PASSWORD (ejecute seed_dev_data primero o exporte la variable).'
            )
            return

        results = []
        try:
            admin = User.objects.get(username=admin_user)
            cliente = User.objects.get(username=client_user)
            moto = Moto.objects.filter(modelo='Moto Dev 2024').first()
            if not moto:
                raise RuntimeError('Ejecute seed_dev_data antes de verify_local_flow.')

            # --- Flujo cliente (services) ---
            carrito, _ = CarritoService.obtener_o_crear_activo(cliente)
            if carrito.estado != 'activo':
                carrito = CarritoCompras.objects.create(
                    id_usuario_cliente=cliente, estado='activo',
                )
            item = CarritoService.agregar_item(
                carrito, cliente, id_moto=moto.id_moto, cantidad=1,
            )
            results.append(('Precio desde BD', item.precio_unitario == moto.precio))
            results.append(('Subtotal backend', item.subtotal == moto.precio))

            pedido = PedidoService.crear_desde_carrito(cliente, carrito)
            results.append(('Total pedido backend', pedido.total == moto.precio))
            carrito.refresh_from_db()
            results.append(('Carrito procesado', carrito.estado == 'procesado'))

            try:
                PedidoService.crear_desde_carrito(cliente, carrito)
                results.append(('Un pedido por carrito', False))
            except BusinessError:
                results.append(('Un pedido por carrito', True))

            PedidoService.confirmar(pedido, cliente)
            results.append(('Pedido confirmado', pedido.estado == 'confirmed'))

            stock_antes = moto.stock
            venta = VentaService.crear_venta_desde_pedido(pedido.pk, admin)
            pedido.refresh_from_db()
            moto.refresh_from_db()
            results.append(('Pedido sigue confirmed', pedido.estado == 'confirmed'))
            results.append(('Venta creada', venta is not None))
            results.append(('Stock disminuido', moto.stock == stock_antes - 1))
            results.append((
                'Movimiento inventario',
                MovimientoInventario.objects.filter(tipo_movimiento='venta').exists(),
            ))
            results.append((
                'Historial venta',
                HistorialEstadoVenta.objects.filter(id_venta=venta).exists(),
            ))
            results.append((
                'Notificación venta',
                Notificacion.objects.filter(id_usuario=cliente).exists(),
            ))
            results.append(('Total venta desde BD', venta.total_venta == moto.precio))

            # --- Financiamiento (antes de pagos adicionales; monto = total - entrada) ---
            entrada_fin = Decimal('500.00')
            monto_fin = venta.total_venta - entrada_fin
            fin = FinanciamientoService.crear(
                venta=venta,
                entidad_financiera='Banco Dev',
                monto_financiado=monto_fin,
                tasa_interes=Decimal('12.00'),
                plazo_meses=12,
                entrada=entrada_fin,
            )
            results.append(('Financiamiento creado', fin is not None))
            results.append(('Saldo pendiente >= 0', fin.saldo_pendiente >= 0))
            results.append(('Cuota calculada', fin.cuota_mensual > 0))
            try:
                FinanciamientoService.crear(
                    venta=venta,
                    entidad_financiera='Duplicado',
                    monto_financiado=Decimal('100.00'),
                    tasa_interes=Decimal('1'),
                    plazo_meses=1,
                    entrada=Decimal('0'),
                )
                results.append(('Segundo financiamiento rechazado', False))
            except BusinessError:
                results.append(('Segundo financiamiento rechazado', True))

            # --- Pago ---
            pago = PagoService.registrar_pago(
                venta=venta,
                monto=Decimal('2000.00'),
                metodo_pago='efectivo',
                tipo_pago='abono',
                procesado_por=admin,
                id_financiamiento=fin.id_financiamiento,
            )
            results.append(('Pago registrado', pago.estado == 'completado'))
            results.append((
                'Total pagado coherente',
                VentaService.total_pagado(venta) == Decimal('2000.00'),
            ))
            fin.refresh_from_db()
            results.append(('Saldo financiamiento actualizado', fin.saldo_pendiente >= 0))

            # --- Factura ---
            factura = FacturaService.emitir(pago, procesado_por=admin)
            results.append(('Factura número autogenerado', factura.numero_factura.startswith('FAC-')))
            results.append(('Factura total = pago', factura.total == pago.monto))
            base, iva, total = descomponer_total_con_iva(pago.monto)
            results.append(('IVA no duplicado', factura.subtotal == base and factura.iva == iva))

            # --- Documento multipart ---
            api = APIClient()
            api.force_authenticate(user=admin)
            archivo = SimpleUploadedFile(
                'contrato.pdf', b'%PDF-1.4 dev', content_type='application/pdf',
            )
            doc_resp = api.post(
                '/api/documentos-venta/',
                {
                    'id_venta': venta.id_venta,
                    'tipo_documento': 'contrato',
                    'archivo': archivo,
                },
                format='multipart',
            )
            results.append(('POST documento', doc_resp.status_code == status.HTTP_201_CREATED))
            doc_id = doc_resp.data.get('id_documento')
            dl = api.get(f'/api/documentos-venta/{doc_id}/archivo/')
            results.append(('GET documento archivo', dl.status_code == status.HTTP_200_OK))

            api.force_authenticate(user=User.objects.create_user(
                'ajeno_verify', 'ajeno@v.local', password,
            ))
            dl_ajeno = api.get(f'/api/documentos-venta/{doc_id}/archivo/')
            results.append(('Cliente ajeno bloqueado', dl_ajeno.status_code in (403, 404)))

            api.force_authenticate(user=admin)
            legacy_resp = api.post(
                '/api/documentos-venta/',
                {
                    'id_venta': venta.id_venta,
                    'tipo_documento': 'otro',
                    'archivo_url_legacy': 'http://evil.com/x',
                },
                format='json',
            )
            results.append((
                'archivo_url_legacy read-only',
                legacy_resp.status_code == status.HTTP_400_BAD_REQUEST
                or 'archivo_url_legacy' not in (legacy_resp.data or {}),
            ))

            # --- Devolución ---
            dev = DevolucionService.solicitar(
                venta, cliente, 'Prueba verify local', Decimal('0'),
            )
            DevolucionService.cambiar_estado(dev, 'aprobada', admin)
            dev.refresh_from_db()
            moto.refresh_from_db()
            results.append(('Devolución stock reintegrado', dev.stock_reintegrado is True))
            results.append(('Reembolso cero sin pagos extra', dev.monto_reembolso_aplicado == 0))
            try:
                DevolucionService.cambiar_estado(dev, 'aprobada', admin)
                results.append(('Segunda aprobación rechazada', False))
            except BusinessError:
                results.append(('Segunda aprobación rechazada', True))

            # --- Mantenimiento ---
            from motoshop.models.repuesto import Repuesto
            from motoshop.models.servicio import Servicio

            rep = Repuesto.objects.get(sku='REP-DEV-001')
            srv = Servicio.objects.get(nombre='Servicio Taller Dev')
            stock_rep_antes = rep.stock
            subtotal_rep = rep.precio_venta * 2
            mant = Mantenimiento.objects.create(
                usuario_cliente=cliente,
                servicio=srv,
                moto=moto,
                kilometraje_actual=1200,
                costo_final=Decimal('45.00'),
                estado='En proceso',
            )
            RepuestoMantenimiento.objects.create(
                mantenimiento=mant,
                repuesto=rep,
                cantidad=2,
                precio_unitario=rep.precio_venta,
                subtotal=subtotal_rep,
            )
            MantenimientoService.cambiar_estado(mant, 'Finalizado', admin)
            rep.refresh_from_db()
            mant.refresh_from_db()
            results.append(('Mantenimiento finalizado', mant.estado == 'Finalizado'))
            results.append(('Repuestos descontados', rep.stock == stock_rep_antes - 2))
            results.append(('Flag repuestos_descontados', mant.repuestos_descontados is True))
            try:
                MantenimientoService.cambiar_estado(mant, 'Finalizado', admin)
                results.append(('Doble descuento rechazado', False))
            except BusinessError:
                results.append(('Doble descuento rechazado', True))

            # --- Endpoints HTTP ---
            api.force_authenticate(user=cliente)
            carrito2, _ = CarritoService.obtener_o_crear_activo(cliente)
            r_car = api.post('/api/carritos/', {'estado': 'activo'}, format='json')
            results.append(('POST /api/carritos/', r_car.status_code in (200, 201)))

            endpoints = [
                ('GET resumen venta', f'/api/ventas/{venta.id_venta}/resumen/', 'get', cliente, (200,)),
                ('GET historial', '/api/historial-estado-venta/', 'get', admin, (200,)),
            ]
            for label, url, method, user, ok_codes in endpoints:
                api.force_authenticate(user=user)
                fn = getattr(api, method)
                resp = fn(url)
                results.append((label, resp.status_code in ok_codes))

        except Exception as exc:
            self.stderr.write(self.style.ERROR(f'Error durante verificación: {exc}'))
            raise

        self.stdout.write(self.style.MIGRATE_HEADING('=== Verificación flujo comercial local ==='))
        failed = 0
        for name, ok in results:
            if ok:
                self.stdout.write(self.style.SUCCESS(f'  [OK] {name}'))
            else:
                failed += 1
                self.stdout.write(self.style.ERROR(f'  [FAIL] {name}'))

        if failed:
            self.stderr.write(self.style.ERROR(f'\n{failed} comprobación(es) fallida(s).'))
            raise SystemExit(1)
        self.stdout.write(self.style.SUCCESS(f'\nTodas las comprobaciones pasaron ({len(results)}).'))
