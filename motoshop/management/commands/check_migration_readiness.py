"""Reporta datos incompatibles antes de migrar MotoShop."""

import sys
from collections import defaultdict

from django.core.management.base import BaseCommand

from motoshop.models import DocumentoVenta, Financiamiento, Garantia
from motoshop.models.moto import Moto
from motoshop.services.financiamiento_duplicado_service import hay_duplicados_globales


class Command(BaseCommand):
    help = (
        'Detecta financiamientos duplicados, garantías con moto inválida '
        'y estado de documentos legacy. No modifica datos.'
    )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('=== MotoShop: revisión pre-migración ==='))
        dup = self._financiamientos_duplicados()
        garantias = self._garantias_invalidas()
        self._documentos_legacy()

        if dup:
            self.stdout.write(self.style.WARNING(
                '\nPara resolver duplicados:\n'
                '  python manage.py resolve_duplicate_financiamientos --export duplicados.json\n'
                '  python manage.py resolve_duplicate_financiamientos --interactive'
            ))

        if garantias:
            self.stdout.write(self.style.ERROR(
                '\nHay garantías con moto inválida. Corrija antes de migrar 0005.'
            ))
            sys.exit(1)

        if dup:
            self.stdout.write(self.style.ERROR(
                '\nHay financiamientos duplicados. Resuélvalos antes de migración 0007 (unique).'
            ))
            self.stdout.write(self.style.NOTICE(
                'Puede aplicar migración 0005/0006 (campos) mientras existan duplicados; '
                '0007 (UniqueConstraint) requiere datos limpios.'
            ))
            sys.exit(1)

        self.stdout.write(self.style.SUCCESS(
            '\nSin bloqueantes. Orden sugerido:\n'
            '  1. python manage.py migrate motoshop 0005\n'
            '  2. python manage.py migrate motoshop 0006\n'
            '  3. python manage.py check_migration_readiness  (validar unique)\n'
            '  4. python manage.py migrate motoshop 0007'
        ))
        sys.exit(0)

    def _financiamientos_duplicados(self):
        if not hay_duplicados_globales():
            self.stdout.write(self.style.SUCCESS(
                'Financiamientos: sin duplicados por venta (listo para 0007 unique).'
            ))
            return False

        por_venta = defaultdict(list)
        for f in Financiamiento.objects.all().order_by('id_venta_id'):
            por_venta[f.id_venta_id].append(f.id_financiamiento)

        self.stdout.write(self.style.ERROR('Financiamientos duplicados (bloquean migración 0007):'))
        for id_venta, ids in sorted(por_venta.items()):
            if len(ids) > 1:
                self.stdout.write(
                    f'  id_venta={id_venta} | cantidad={len(ids)} | ids={ids}'
                )
        return True

    def _garantias_invalidas(self):
        moto_ids = set(Moto.objects.values_list('id_moto', flat=True))
        invalidas = []
        for g in Garantia.objects.all().order_by('id_garantia'):
            moto_id = getattr(g, 'id_moto_id', None)
            if moto_id is None:
                moto_id = g.id_moto
            if moto_id not in moto_ids:
                invalidas.append((g.id_garantia, moto_id))

        if not invalidas:
            self.stdout.write(self.style.SUCCESS('Garantías: todas las motos referenciadas existen.'))
            return False

        self.stdout.write(self.style.ERROR('Garantías con id_moto inválido:'))
        for id_garantia, moto_id in invalidas:
            self.stdout.write(
                f'  id_garantia={id_garantia} | id_moto={moto_id} | motivo=moto inexistente'
            )
        return True

    def _documentos_legacy(self):
        total = DocumentoVenta.objects.count()
        con_archivo = DocumentoVenta.objects.exclude(archivo='').exclude(archivo__isnull=True).count()
        legacy_field = 'archivo_url_legacy' if hasattr(DocumentoVenta, 'archivo_url_legacy') else 'archivo_url'
        filtro_legacy = {f'{legacy_field}__gt': ''}
        con_legacy = DocumentoVenta.objects.filter(**filtro_legacy).count() if legacy_field else 0
        if legacy_field == 'archivo_url_legacy':
            con_legacy = DocumentoVenta.objects.exclude(archivo_url_legacy='').count()
        else:
            con_legacy = DocumentoVenta.objects.exclude(archivo_url='').count()
        vacios = total - con_archivo - con_legacy
        if vacios < 0:
            vacios = DocumentoVenta.objects.filter(archivo__isnull=True, archivo_url_legacy='').count()

        self.stdout.write('Documentos de venta:')
        self.stdout.write(f'  total: {total}')
        self.stdout.write(f'  con FileField (archivo): {con_archivo}')
        self.stdout.write(f'  con URL legacy: {con_legacy}')
        self.stdout.write(f'  sin archivo ni legacy (aprox.): {max(vacios, 0)}')
