"""Generación de notificaciones desde la lógica de negocio."""

from motoshop.models import Notificacion


class NotificacionService:
    @staticmethod
    def crear(usuario, titulo, mensaje):
        return Notificacion.objects.create(
            id_usuario=usuario,
            titulo=titulo,
            mensaje=mensaje,
        )

    @staticmethod
    def pedido_confirmado(pedido):
        return NotificacionService.crear(
            pedido.id_usuario_cliente,
            'Pedido confirmado',
            f'Tu pedido #{pedido.id_pedido} fue confirmado. Total: ${pedido.total}.',
        )

    @staticmethod
    def venta_creada(venta):
        return NotificacionService.crear(
            venta.id_usuario_cliente,
            'Venta registrada',
            f'Se registró la venta #{venta.id_venta} por ${venta.total_venta}.',
        )

    @staticmethod
    def estado_venta_actualizado(venta, estado_anterior, observacion=''):
        msg = (
            f'La venta #{venta.id_venta} cambió de "{estado_anterior}" a "{venta.estado}".'
        )
        if observacion:
            msg += f' {observacion}'
        return NotificacionService.crear(
            venta.id_usuario_cliente,
            'Estado de venta actualizado',
            msg,
        )

    @staticmethod
    def pago_registrado(pago):
        return NotificacionService.crear(
            pago.id_venta.id_usuario_cliente,
            'Pago registrado',
            f'Se registró un pago de ${pago.monto} para la venta #{pago.id_venta_id}.',
        )

    @staticmethod
    def financiamiento_pagado(financiamiento):
        return NotificacionService.crear(
            financiamiento.id_venta.id_usuario_cliente,
            'Financiamiento saldado',
            f'El financiamiento #{financiamiento.id_financiamiento} fue pagado en su totalidad.',
        )

    @staticmethod
    def factura_emitida(factura):
        venta = factura.id_pago.id_venta
        return NotificacionService.crear(
            venta.id_usuario_cliente,
            'Factura emitida',
            f'Se emitió la factura #{factura.numero_factura} por ${factura.total} '
            f'(pago #{factura.id_pago_id}, venta #{venta.id_venta}).',
        )

    @staticmethod
    def documento_disponible(documento):
        return NotificacionService.crear(
            documento.id_venta.id_usuario_cliente,
            'Documento disponible',
            f'Nuevo documento "{documento.tipo_documento}" disponible para tu venta '
            f'#{documento.id_venta_id}.',
        )

    @staticmethod
    def devolucion_resuelta(devolucion, aprobada):
        titulo = 'Devolución aprobada' if aprobada else 'Devolución rechazada'
        return NotificacionService.crear(
            devolucion.id_venta.id_usuario_cliente,
            titulo,
            f'Tu solicitud de devolución #{devolucion.id_devolucion} fue '
            f'{"aprobada" if aprobada else "rechazada"}.',
        )

    @staticmethod
    def mantenimiento_finalizado(mantenimiento):
        return NotificacionService.crear(
            mantenimiento.usuario_cliente,
            'Mantenimiento finalizado',
            f'El mantenimiento #{mantenimiento.id_mantenimiento} de tu moto '
            f'{mantenimiento.moto} fue finalizado.',
        )
