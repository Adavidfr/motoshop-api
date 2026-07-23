"""Utilidades de test para simular financiamientos duplicados (estado pre-migración 0007)."""

from django.db import connection


def quitar_unique_financiamiento_por_venta():
    """
    Elimina temporalmente UniqueConstraint id_venta en la BD de prueba.

    La migración 0007 crea el constraint; los tests de resolución de duplicados
    necesitan insertar más de un financiamiento por venta.
    """
    with connection.cursor() as cursor:
        if connection.vendor == 'sqlite':
            cursor.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name='financiamientos'"
            )
            row = cursor.fetchone()
            if not row or 'uniq_financiamiento_por_venta' not in row[0]:
                return
            create_sql = row[0]
            new_sql = create_sql.replace(
                ', CONSTRAINT "uniq_financiamiento_por_venta" UNIQUE ("id_venta")',
                '',
            ).replace(
                'CREATE TABLE "financiamientos"',
                'CREATE TABLE "financiamientos_new"',
            )
            cursor.execute(new_sql)
            cursor.execute(
                'INSERT INTO financiamientos_new SELECT * FROM financiamientos'
            )
            cursor.execute('DROP TABLE financiamientos')
            cursor.execute('ALTER TABLE financiamientos_new RENAME TO financiamientos')
            cursor.execute(
                'CREATE INDEX IF NOT EXISTS "financiamientos_id_venta_83a9d127" '
                'ON "financiamientos" ("id_venta")'
            )
        elif connection.vendor == 'postgresql':
            cursor.execute(
                'ALTER TABLE financiamientos '
                'DROP CONSTRAINT IF EXISTS uniq_financiamiento_por_venta'
            )
        else:
            raise NotImplementedError(
                f'quitar_unique_financiamiento_por_venta no soporta {connection.vendor}'
            )
