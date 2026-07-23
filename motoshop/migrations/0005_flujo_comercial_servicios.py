# Generated manually for flujo comercial — validación estricta pre-PostgreSQL

from collections import Counter, defaultdict

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class MigrationPreconditionError(Exception):
    """Datos incompatibles detectados antes de aplicar cambios estructurales."""


def _reportar_financiamientos_duplicados(apps):
    Financiamiento = apps.get_model('motoshop', 'Financiamiento')
    por_venta = defaultdict(list)
    for f in Financiamiento.objects.all().order_by('id_venta_id', 'id_financiamiento'):
        por_venta[f.id_venta_id].append(f.id_financiamiento)

    duplicados = {v: ids for v, ids in por_venta.items() if len(ids) > 1}
    if not duplicados:
        return []

    lineas = ['Financiamientos duplicados por venta (resolver manualmente):']
    for id_venta, ids in sorted(duplicados.items()):
        lineas.append(
            f'  - id_venta={id_venta}: {len(ids)} financiamiento(s), ids={ids}'
        )
    return lineas


def _reportar_garantias_invalidas(apps):
    Garantia = apps.get_model('motoshop', 'Garantia')
    Moto = apps.get_model('motoshop', 'Moto')
    moto_ids = set(Moto.objects.values_list('id_moto', flat=True))

    invalidas = []
    for g in Garantia.objects.all().order_by('id_garantia'):
        moto_val = g.id_moto
        if moto_val not in moto_ids:
            invalidas.append(
                f'  - id_garantia={g.id_garantia}, id_moto={moto_val} '
                f'(moto inexistente en tabla motos)'
            )
    if not invalidas:
        return []
    return ['Garantías con id_moto inválido (corregir antes de FK):', *invalidas]


def _reportar_documentos_legacy(apps):
    DocumentoVenta = apps.get_model('motoshop', 'DocumentoVenta')
    total = DocumentoVenta.objects.count()
    if total == 0:
        return []

    # Antes del rename, el campo aún se llama archivo_url
    con_legacy = DocumentoVenta.objects.exclude(archivo_url='').exclude(archivo_url__isnull=True).count()
    sin_nada = DocumentoVenta.objects.filter(archivo_url='').count()
    return [
        'Documentos de venta (pre-migración):',
        f'  - total registros: {total}',
        f'  - con URL legacy (archivo_url): {con_legacy}',
        f'  - sin URL (vacíos): {sin_nada}',
        f'  - con FileField: 0 (campo aún no existe)',
    ]


def validar_datos_pre_migracion(apps, schema_editor):
    errores = []
    advertencias = _reportar_financiamientos_duplicados(apps)
    errores.extend(_reportar_garantias_invalidas(apps))
    info = _reportar_documentos_legacy(apps)

    for linea in info:
        print(linea)
    for linea in advertencias:
        print(f'ADVERTENCIA: {linea}')
        print(
            '  → Ejecute: python manage.py resolve_duplicate_financiamientos --export duplicados.json'
        )

    if errores:
        mensaje = (
            'Migración 0005 abortada: datos incompatibles detectados.\n'
            'Ejecute: python manage.py check_migration_readiness\n\n'
            + '\n'.join(errores)
        )
        raise MigrationPreconditionError(mensaje)


def inicializar_saldo_financiamiento(apps, schema_editor):
    Financiamiento = apps.get_model('motoshop', 'Financiamiento')
    for f in Financiamiento.objects.all():
        if f.saldo_pendiente is None or f.saldo_pendiente == 0:
            f.saldo_pendiente = f.monto_financiado
            f.save(update_fields=['saldo_pendiente'])


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('motoshop', '0004_clienteperfil_foto_perfil_moto_imagen_and_more'),
    ]

    operations = [
        migrations.RunPython(validar_datos_pre_migracion, migrations.RunPython.noop),
        migrations.AddField(
            model_name='compra',
            name='stock_aplicado',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='mantenimiento',
            name='repuestos_descontados',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='financiamiento',
            name='entrada',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name='financiamiento',
            name='saldo_pendiente',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.RunPython(inicializar_saldo_financiamiento, migrations.RunPython.noop),
        migrations.AddField(
            model_name='pago',
            name='tipo_pago',
            field=models.CharField(
                choices=[
                    ('contado', 'Contado'),
                    ('entrada', 'Entrada'),
                    ('cuota', 'Cuota'),
                    ('abono', 'Abono'),
                    ('reembolso', 'Reembolso'),
                ],
                default='contado',
                max_length=30,
            ),
        ),
        migrations.AddField(
            model_name='pago',
            name='comprobante',
            field=models.FileField(blank=True, null=True, upload_to='comprobantes_pago/'),
        ),
        migrations.AddField(
            model_name='pago',
            name='id_financiamiento',
            field=models.ForeignKey(
                blank=True,
                db_column='id_financiamiento',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='pagos',
                to='motoshop.financiamiento',
            ),
        ),
        migrations.AddField(
            model_name='pago',
            name='procesado_por',
            field=models.ForeignKey(
                blank=True,
                db_column='id_usuario_procesador',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='pagos_procesados',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RenameField(
            model_name='documentoventa',
            old_name='archivo_url',
            new_name='archivo_url_legacy',
        ),
        migrations.AddField(
            model_name='documentoventa',
            name='archivo',
            field=models.FileField(blank=True, null=True, upload_to='documentos_venta/'),
        ),
        migrations.AddField(
            model_name='documentoventa',
            name='content_type',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AddField(
            model_name='documentoventa',
            name='nombre_original',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AddField(
            model_name='documentoventa',
            name='subido_por',
            field=models.ForeignKey(
                blank=True,
                db_column='id_usuario_subidor',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='documentos_subidos',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='documentoventa',
            name='tamano_bytes',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='historialestadoventa',
            name='id_usuario',
            field=models.ForeignKey(
                blank=True,
                db_column='id_usuario',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='historial_ventas_registradas',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name='garantia',
            name='id_moto',
            field=models.ForeignKey(
                db_column='id_moto',
                on_delete=django.db.models.deletion.PROTECT,
                related_name='garantias',
                to='motoshop.moto',
            ),
        ),
    ]
