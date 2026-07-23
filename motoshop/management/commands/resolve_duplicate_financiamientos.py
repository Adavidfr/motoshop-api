"""
Resolución segura de financiamientos duplicados por venta (pre-migración 0007).

Modo lectura (default):
  python manage.py resolve_duplicate_financiamientos
  python manage.py resolve_duplicate_financiamientos --check

Exportar:
  python manage.py resolve_duplicate_financiamientos --export reporte_financiamientos.json

Interactivo (modifica datos con confirmaciones):
  python manage.py resolve_duplicate_financiamientos --interactive
"""

import getpass
import json
import sys

from django.core.management.base import BaseCommand, CommandError

from motoshop.services.financiamiento_duplicado_service import (
    ConfirmacionInvalida,
    ResolucionAbortada,
    cancelar_duplicados,
    detectar_duplicados,
    exportar_reporte,
    respaldar_y_eliminar_duplicados,
)
from motoshop.utils.financiamiento_audit import nuevo_archivo_auditoria


class Command(BaseCommand):
    help = 'Diagnostica y resuelve financiamientos duplicados por venta antes de migración 0007.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--check',
            action='store_true',
            help='Solo diagnóstico (equivalente al modo por defecto).',
        )
        parser.add_argument(
            '--export',
            metavar='RUTA',
            help='Exporta reporte JSON (ej. reporte_financiamientos.json).',
        )
        parser.add_argument(
            '--interactive',
            action='store_true',
            help='Modo interactivo controlado con confirmaciones explícitas.',
        )

    def handle(self, *args, **options):
        if options['interactive']:
            return self._modo_interactivo()

        duplicadas, resumen = detectar_duplicados()
        self._imprimir_diagnostico(duplicadas, resumen)

        if options['export']:
            ruta, _ = exportar_reporte(options['export'])
            self.stdout.write(self.style.SUCCESS(f'Reporte exportado: {ruta}'))

        if resumen['ventas_con_duplicados'] > 0:
            self.stdout.write(self.style.WARNING(
                '\nEjecute:\n'
                '  python manage.py resolve_duplicate_financiamientos --export duplicados.json\n'
                '  python manage.py resolve_duplicate_financiamientos --interactive'
            ))
            sys.exit(1)

        self.stdout.write(self.style.SUCCESS('\nNo hay duplicados. Listo para migración 0007 (unique).'))
        sys.exit(0)

    def _imprimir_diagnostico(self, duplicadas, resumen):
        self.stdout.write(self.style.MIGRATE_HEADING(
            '=== MotoShop: financiamientos duplicados por venta ==='
        ))

        if not duplicadas:
            self.stdout.write(self.style.SUCCESS('No se encontraron ventas con duplicados.'))
        else:
            for venta in duplicadas:
                self.stdout.write('')
                self.stdout.write(self.style.WARNING(f"--- Venta #{venta['id_venta']} ---"))
                self.stdout.write(f"  Cliente: {venta['cliente']['username']} ({venta['cliente']['email']})")
                self.stdout.write(f"  Total venta: {venta['total_venta']} | Estado: {venta['estado_venta']}")
                self.stdout.write(f"  Financiamientos: {venta['cantidad_financiamientos']}")
                self.stdout.write(
                    f"  Sugerido conservar ID {venta['sugerido_conservar_id']}: "
                    f"{venta['sugerido_justificacion']}"
                )
                if venta['pagos_nota_global']:
                    self.stdout.write(self.style.NOTICE(f"  {venta['pagos_nota_global']}"))
                for fin in venta['financiamientos']:
                    self.stdout.write(
                        f"    Fin #{fin['id_financiamiento']} | {fin['estado']} | "
                        f"monto={fin['monto_financiado']} | entrada={fin['entrada']} | "
                        f"saldo={fin['saldo_pendiente']} | pagos_rel={fin['cantidad_pagos_relacionados']} | "
                        f"pagado_rel={fin['total_pagado_relacionado']}"
                    )
                    if not fin['pagos_asignacion_concluyente']:
                        self.stdout.write(self.style.NOTICE(
                            f"      Asignación pagos→financiamiento: NO concluyente"
                        ))
                    for adv in fin['advertencias']:
                        self.stdout.write(self.style.ERROR(f'      ⚠ {adv}'))
                for adv in venta['advertencias']:
                    self.stdout.write(self.style.ERROR(f'  ⚠ Venta: {adv}'))
                for acc in venta['acciones_sugeridas']:
                    self.stdout.write(f'  → {acc}')

        self.stdout.write('')
        self.stdout.write('--- Resumen ---')
        for k, v in resumen.items():
            label = k.replace('_', ' ').capitalize()
            self.stdout.write(f'  {label}: {v}')

    def _modo_interactivo(self):
        duplicadas, resumen = detectar_duplicados()
        self._imprimir_diagnostico(duplicadas, resumen)

        if not duplicadas:
            self.stdout.write(self.style.SUCCESS('Nada que resolver.'))
            return

        usuario = getpass.getuser()
        audit_path = nuevo_archivo_auditoria()
        self.stdout.write(f'Auditoría: {audit_path}')

        for venta in duplicadas:
            id_venta = venta['id_venta']
            self.stdout.write(self.style.MIGRATE_HEADING(f'\n=== Resolver venta #{id_venta} ==='))
            self.stdout.write(
                f"Sugerido conservar ID {venta['sugerido_conservar_id']}: "
                f"{venta['sugerido_justificacion']}"
            )
            self.stdout.write(
                '\nOpciones:\n'
                '  1. Conservar uno y cancelar los demás (recomendado; requiere paso de archivo/eliminación)\n'
                '  2. Conservar uno y eliminar los demás (tras respaldo; destructivo)\n'
                '  3. Fusionar manualmente (solo instrucciones; omitir)\n'
                '  4. Omitir esta venta\n'
                '  5. Salir sin continuar'
            )
            opcion = input('Seleccione opción [1-5]: ').strip()

            if opcion == '5':
                self.stdout.write('Salida sin cambios adicionales.')
                break
            if opcion == '4':
                continue
            if opcion == '3':
                self.stdout.write(
                    'Fusión manual: edite registros en admin/SQL, deje un solo financiamiento '
                    f'por venta #{id_venta}, luego re-ejecute diagnóstico.'
                )
                continue
            if opcion not in ('1', '2'):
                self.stdout.write('Opción inválida; venta omitida.')
                continue

            confirm = input(f'Escriba CONFIRMAR VENTA {id_venta}: ').strip()
            if confirm != f'CONFIRMAR VENTA {id_venta}':
                self.stdout.write(self.style.ERROR('Confirmación inválida; venta omitida.'))
                continue

            conservar_raw = input(
                f'ID de financiamiento a CONSERVAR (sugerido {venta["sugerido_conservar_id"]}): '
            ).strip()
            try:
                conservar_id = int(conservar_raw)
            except ValueError:
                self.stdout.write(self.style.ERROR('ID inválido; venta omitida.'))
                continue

            try:
                if opcion == '1':
                    cancelar_duplicados(id_venta, conservar_id, usuario, audit_path)
                    self.stdout.write(self.style.SUCCESS(
                        f'Duplicados cancelados. IMPORTANTE: cancelar no basta para unique id_venta.'
                    ))
                    self.stdout.write(
                        'Debe respaldar y eliminar duplicados cancelados, o la migración 0007 fallará.'
                    )
                    if input('¿Respaldar y eliminar duplicados cancelados ahora? [s/N]: ').strip().lower() == 's':
                        self._eliminar_con_confirmacion(id_venta, conservar_id, usuario, audit_path)
                elif opcion == '2':
                    self._eliminar_con_confirmacion(id_venta, conservar_id, usuario, audit_path)
            except (ConfirmacionInvalida, ResolucionAbortada) as exc:
                self.stdout.write(self.style.ERROR(str(exc)))
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f'Error (rollback aplicado): {exc}'))

        self.stdout.write(self.style.SUCCESS(f'\nAuditoría guardada en: {audit_path}'))

    def _eliminar_con_confirmacion(self, id_venta, conservar_id, usuario, audit_path):
        from motoshop.services.financiamiento_duplicado_service import venta_tiene_duplicados
        if not venta_tiene_duplicados(id_venta):
            self.stdout.write('La venta ya no tiene duplicados.')
            return

        from motoshop.models import Financiamiento
        duplicados = [
            f.id_financiamiento for f in Financiamiento.objects.filter(id_venta_id=id_venta)
            if f.id_financiamiento != conservar_id
        ]
        for fin_id in duplicados:
            confirm = input(f'Escriba ELIMINAR FINANCIAMIENTO {fin_id}: ').strip()
            if confirm != f'ELIMINAR FINANCIAMIENTO {fin_id}':
                raise ConfirmacionInvalida(f'Confirmación rechazada para #{fin_id}.')

        entrada = respaldar_y_eliminar_duplicados(id_venta, conservar_id, usuario, audit_path)
        self.stdout.write(self.style.SUCCESS(
            f"Eliminados {len(entrada['financiamientos_eliminados'])} duplicado(s) tras respaldo."
        ))
