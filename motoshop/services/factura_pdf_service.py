"""Generación de PDF para facturas emitidas."""

from io import BytesIO

from django.conf import settings
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from motoshop.utils.facturacion import obtener_tasa_iva


class FacturaPdfService:
    @classmethod
    def generar(cls, factura) -> bytes:
        """Genera bytes PDF para una instancia de Factura con relaciones precargadas."""
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
            title=factura.numero_factura,
        )

        pago = factura.id_pago
        venta = pago.id_venta
        cliente = venta.id_usuario_cliente
        vendedor = venta.id_usuario_vendedor
        pedido_id = venta.id_pedido_id

        empresa = getattr(settings, 'MOTOSHOP_EMPRESA_NOMBRE', 'MotoShop')
        ruc = getattr(settings, 'MOTOSHOP_EMPRESA_RUC', '')
        tasa_iva = obtener_tasa_iva()

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'FacturaTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=6,
        )
        subtitle_style = ParagraphStyle(
            'FacturaSubtitle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.grey,
        )

        fecha = timezone.localtime(factura.fecha_emision).strftime('%d/%m/%Y %H:%M')

        story = [
            Paragraph(empresa, title_style),
        ]
        if ruc:
            story.append(Paragraph(f'RUC: {ruc}', subtitle_style))
        story.extend([
            Spacer(1, 0.4 * cm),
            Paragraph(f'<b>FACTURA {factura.numero_factura}</b>', styles['Heading2']),
            Paragraph(f'Fecha de emisión: {fecha}', styles['Normal']),
            Spacer(1, 0.6 * cm),
        ])

        meta_data = [
            ['Cliente', cliente.get_full_name() or cliente.username],
            ['Usuario cliente', cliente.username],
            ['Email', cliente.email or '—'],
            ['Venta', f'#{venta.id_venta}'],
            ['Pedido', f'#{pedido_id}' if pedido_id else '—'],
            ['Pago', f'#{pago.id_pago}'],
            ['Método de pago', pago.get_metodo_pago_display()],
            ['Tipo de pago', pago.get_tipo_pago_display()],
            ['Vendedor', vendedor.username if vendedor else '—'],
        ]
        meta_table = Table(meta_data, colWidths=[4.5 * cm, 11 * cm])
        meta_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.extend([meta_table, Spacer(1, 0.8 * cm)])

        detalle_data = [
            ['Concepto', 'Monto'],
            [
                f'Pago recibido — Venta #{venta.id_venta} / Pago #{pago.id_pago}',
                f'${factura.total:,.2f}',
            ],
        ]
        detalle_table = Table(detalle_data, colWidths=[12 * cm, 3.5 * cm])
        detalle_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1a1a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.extend([detalle_table, Spacer(1, 0.5 * cm)])

        totales_data = [
            ['Subtotal', f'${factura.subtotal:,.2f}'],
            [f'IVA ({tasa_iva * 100:.0f}%)', f'${factura.iva:,.2f}'],
            ['Total', f'${factura.total:,.2f}'],
        ]
        totales_table = Table(totales_data, colWidths=[12 * cm, 3.5 * cm])
        totales_table.setStyle(TableStyle([
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.extend([
            totales_table,
            Spacer(1, 1 * cm),
            Paragraph(
                'Documento generado electrónicamente. Corresponde al monto del pago registrado.',
                subtitle_style,
            ),
        ])

        doc.build(story)
        return buffer.getvalue()

    @classmethod
    def nombre_archivo(cls, factura) -> str:
        return f'{factura.numero_factura}.pdf'
