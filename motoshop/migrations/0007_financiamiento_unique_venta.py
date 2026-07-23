# UniqueConstraint Financiamiento.id_venta — aplicar tras limpiar duplicados (0007)

from collections import defaultdict

from django.db import migrations, models


class MigrationPreconditionError(Exception):
    pass


def validar_sin_duplicados_financiamiento(apps, schema_editor):
    Financiamiento = apps.get_model('motoshop', 'Financiamiento')
    por_venta = defaultdict(list)
    for f in Financiamiento.objects.all().order_by('id_venta_id'):
        por_venta[f.id_venta_id].append(f.id_financiamiento)

    duplicados = {v: ids for v, ids in por_venta.items() if len(ids) > 1}
    if duplicados:
        lineas = [
            'Migración 0007 abortada: aún existen financiamientos duplicados por venta.',
            'Ejecute:',
            '  python manage.py resolve_duplicate_financiamientos --export duplicados.json',
            '  python manage.py resolve_duplicate_financiamientos --interactive',
            '',
        ]
        for id_venta, ids in sorted(duplicados.items()):
            lineas.append(f'  id_venta={id_venta} | ids={ids}')
        raise MigrationPreconditionError('\n'.join(lineas))


class Migration(migrations.Migration):

    dependencies = [
        ('motoshop', '0006_devolucion_idempotencia'),
    ]

    operations = [
        migrations.RunPython(validar_sin_duplicados_financiamiento, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name='financiamiento',
            constraint=models.UniqueConstraint(
                fields=('id_venta',),
                name='uniq_financiamiento_por_venta',
            ),
        ),
    ]
