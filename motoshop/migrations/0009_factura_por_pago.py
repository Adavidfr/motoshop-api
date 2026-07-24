# Generated migration: Factura vinculada a Pago (1 factura por pago)

from django.db import migrations, models
import django.db.models.deletion


def vincular_facturas_a_pagos(apps, schema_editor):
    """Migra facturas existentes (1 por venta) al primer pago completado de cada venta."""
    Factura = apps.get_model('motoshop', 'Factura')
    Pago = apps.get_model('motoshop', 'Pago')

    for factura in Factura.objects.select_related('id_venta').all():
        venta_id = factura.id_venta_id
        pago = (
            Pago.objects
            .filter(id_venta_id=venta_id, estado='completado')
            .exclude(tipo_pago='reembolso')
            .order_by('id_pago')
            .first()
        )
        if pago is None:
            pago = Pago.objects.create(
                id_venta_id=venta_id,
                monto=factura.total,
                metodo_pago='efectivo',
                tipo_pago='contado',
                estado='completado',
            )
        factura.id_pago = pago
        factura.save(update_fields=['id_pago'])


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ('motoshop', '0008_alter_documentoventa_archivo_url_legacy'),
    ]

    operations = [
        migrations.AddField(
            model_name='factura',
            name='id_pago',
            field=models.OneToOneField(
                blank=True,
                db_column='id_pago',
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='factura',
                to='motoshop.pago',
            ),
        ),
        migrations.RunPython(vincular_facturas_a_pagos, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='factura',
            name='id_venta',
        ),
        migrations.AlterField(
            model_name='factura',
            name='id_pago',
            field=models.OneToOneField(
                db_column='id_pago',
                on_delete=django.db.models.deletion.PROTECT,
                related_name='factura',
                to='motoshop.pago',
            ),
        ),
    ]
