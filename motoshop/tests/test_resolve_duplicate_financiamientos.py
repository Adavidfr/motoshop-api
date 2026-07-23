"""Pruebas para resolución de financiamientos duplicados."""

import json
import tempfile
from decimal import Decimal
from io import StringIO
from pathlib import Path
from unittest import mock

from django.contrib.auth.models import User
from django.core.management import call_command
from django.db import connection
from django.test import TestCase, TransactionTestCase, override_settings, tag

from motoshop.models import Financiamiento, Pago, Venta
from motoshop.models.carrito_compras import CarritoCompras
from motoshop.models.pedido import Pedido
from motoshop.services.financiamiento_duplicado_service import (
    ConfirmacionInvalida,
    cancelar_duplicados,
    detectar_duplicados,
    exportar_reporte,
    hay_duplicados_globales,
    respaldar_y_eliminar_duplicados,
    sugerir_conservar,
    venta_tiene_duplicados,
)
from motoshop.tests.financiamiento_duplicado_helpers import quitar_unique_financiamiento_por_venta


@override_settings(
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
)
class FinanciamientoDuplicadoServiceTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        quitar_unique_financiamiento_por_venta()

    def setUp(self):
        self.staff = User.objects.create_user('adm', 'a@t.com', 'x', is_staff=True)
        self.cliente = User.objects.create_user('cli', 'c@t.com', 'x')
        cart = CarritoCompras.objects.create(id_usuario_cliente=self.cliente, estado='procesado')
        pedido = Pedido.objects.create(
            id_usuario_cliente=self.cliente, id_carrito=cart,
            total=Decimal('10000'), estado='confirmed',
        )
        self.venta = Venta.objects.create(
            id_pedido=pedido, id_usuario_cliente=self.cliente,
            id_usuario_vendedor=self.staff, total_venta=Decimal('10000'), estado='pendiente',
        )

    def _crear_fin(self, monto, estado='activo', pk_suffix=1):
        return Financiamiento.objects.create(
            id_venta=self.venta,
            entidad_financiera=f'Banco {pk_suffix}',
            monto_financiado=Decimal(str(monto)),
            tasa_interes=Decimal('10'),
            plazo_meses=12,
            cuota_mensual=Decimal('100'),
            entrada=Decimal('0'),
            saldo_pendiente=Decimal(str(monto)),
            estado=estado,
        )

    def test_sin_duplicados(self):
        self._crear_fin(5000)
        self.assertFalse(hay_duplicados_globales())
        dup, resumen = detectar_duplicados()
        self.assertEqual(resumen['ventas_con_duplicados'], 0)

    def test_diagnostico_con_duplicados(self):
        f1 = self._crear_fin(5000, pk_suffix=1)
        self._crear_fin(5000, pk_suffix=2)
        Pago.objects.create(
            id_venta=self.venta, id_financiamiento=f1,
            monto=Decimal('200'), metodo_pago='efectivo',
            estado='completado', tipo_pago='cuota', procesado_por=self.staff,
        )
        dup, resumen = detectar_duplicados()
        self.assertEqual(resumen['ventas_con_duplicados'], 1)
        self.assertEqual(len(dup[0]['financiamientos']), 2)
        self.assertEqual(dup[0]['sugerido_conservar_id'], f1.id_financiamiento)

    def test_sugerencia_prefiere_financiamiento_con_pagos(self):
        self._crear_fin(3000, pk_suffix=1)
        f2 = self._crear_fin(7000, pk_suffix=2)
        Pago.objects.create(
            id_venta=self.venta, id_financiamiento=f2,
            monto=Decimal('500'), metodo_pago='efectivo',
            estado='completado', tipo_pago='cuota', procesado_por=self.staff,
        )
        fins = list(Financiamiento.objects.filter(id_venta=self.venta))
        from motoshop.services import financiamiento_duplicado_service as svc
        pagos, tiene_fk = svc._pagos_de_venta(Pago, self.venta.id_venta)
        elegido, _ = sugerir_conservar(fins, self.venta, pagos, tiene_fk)
        self.assertEqual(elegido.id_financiamiento, f2.id_financiamiento)

    def test_exportar_json(self):
        self._crear_fin(1000, pk_suffix=1)
        self._crear_fin(2000, pk_suffix=2)
        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp) / 'reporte.json'
            exportar_reporte(ruta)
            data = json.loads(ruta.read_text(encoding='utf-8'))
            self.assertIn('ventas_duplicadas', data)
            self.assertEqual(data['resumen']['ventas_con_duplicados'], 1)

    def test_cancelar_no_elimina(self):
        f1 = self._crear_fin(1000, pk_suffix=1)
        f2 = self._crear_fin(2000, pk_suffix=2)
        with tempfile.TemporaryDirectory() as tmp:
            audit = Path(tmp) / 'audit.json'
            cancelar_duplicados(self.venta.id_venta, f1.id_financiamiento, 'tester', audit)
            self.assertTrue(audit.exists())
        self.assertEqual(Financiamiento.objects.filter(id_venta=self.venta).count(), 2)
        f2.refresh_from_db()
        self.assertEqual(f2.estado, 'cancelado')
        self.assertEqual(f2.saldo_pendiente, Decimal('0'))

    def test_respaldar_y_eliminar_duplicados(self):
        f1 = self._crear_fin(1000, pk_suffix=1)
        self._crear_fin(2000, pk_suffix=2)
        with tempfile.TemporaryDirectory() as tmp:
            audit = Path(tmp) / 'audit.json'
            respaldar_y_eliminar_duplicados(
                self.venta.id_venta, f1.id_financiamiento, 'tester', audit,
            )
            self.assertEqual(Financiamiento.objects.filter(id_venta=self.venta).count(), 1)
            self.assertTrue(audit.exists())
            payload = json.loads(audit.read_text(encoding='utf-8'))
            self.assertEqual(payload['usuario_ejecutor'], 'tester')
            self.assertEqual(len(payload['entradas']), 1)

    def test_conservar_id_inexistente_raises(self):
        self._crear_fin(1000, pk_suffix=1)
        self._crear_fin(2000, pk_suffix=2)
        with self.assertRaises(ConfirmacionInvalida):
            respaldar_y_eliminar_duplicados(self.venta.id_venta, 99999, 'tester')

    def test_saldo_inconsistente_detectado(self):
        self._crear_fin(15000, pk_suffix=1)
        self._crear_fin(1000, pk_suffix=2)
        dup, _ = detectar_duplicados()
        advertencias = dup[0]['financiamientos'][0]['advertencias']
        self.assertTrue(any('supera total_venta' in a for a in advertencias))

    def test_mas_de_un_activo_advertencia(self):
        self._crear_fin(1000, estado='activo', pk_suffix=1)
        self._crear_fin(2000, estado='activo', pk_suffix=2)
        dup, _ = detectar_duplicados()
        self.assertTrue(
            any('más de un financiamiento activo' in a for a in dup[0]['advertencias'])
        )

    def test_financiamiento_sin_pagos_sugerido_por_estado(self):
        f1 = self._crear_fin(1000, estado='cancelado', pk_suffix=1)
        f2 = self._crear_fin(2000, estado='activo', pk_suffix=2)
        fins = list(Financiamiento.objects.filter(id_venta=self.venta))
        from motoshop.services import financiamiento_duplicado_service as svc
        pagos, tiene_fk = svc._pagos_de_venta(Pago, self.venta.id_venta)
        elegido, razon = sugerir_conservar(fins, self.venta, pagos, tiene_fk)
        self.assertEqual(elegido.id_financiamiento, f2.id_financiamiento)
        self.assertIn('activo', razon)


@override_settings(
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
)
class ResolveDuplicateFinanciamientosCommandTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        quitar_unique_financiamiento_por_venta()

    def setUp(self):
        self.staff = User.objects.create_user('adm2', 'a2@t.com', 'x', is_staff=True)
        self.cliente = User.objects.create_user('cli2', 'c2@t.com', 'x')
        cart = CarritoCompras.objects.create(id_usuario_cliente=self.cliente, estado='procesado')
        pedido = Pedido.objects.create(
            id_usuario_cliente=self.cliente, id_carrito=cart,
            total=Decimal('5000'), estado='confirmed',
        )
        self.venta = Venta.objects.create(
            id_pedido=pedido, id_usuario_cliente=self.cliente,
            id_usuario_vendedor=self.staff, total_venta=Decimal('5000'), estado='pendiente',
        )

    def _crear_par_duplicados(self):
        ids = []
        for i in range(2):
            fin = Financiamiento.objects.create(
                id_venta=self.venta, entidad_financiera=f'B{i}',
                monto_financiado=Decimal('2500'), tasa_interes=Decimal('5'),
                plazo_meses=6, cuota_mensual=Decimal('450'),
                entrada=0, saldo_pendiente=Decimal('2500'), estado='activo',
            )
            ids.append(fin.id_financiamiento)
        return ids

    def test_comando_sin_duplicados_exit_zero(self):
        Financiamiento.objects.create(
            id_venta=self.venta, entidad_financiera='Banco',
            monto_financiado=Decimal('5000'), tasa_interes=Decimal('5'),
            plazo_meses=6, cuota_mensual=Decimal('900'),
            entrada=0, saldo_pendiente=Decimal('5000'), estado='activo',
        )
        with self.assertRaises(SystemExit) as ctx:
            call_command('resolve_duplicate_financiamientos', stdout=StringIO())
        self.assertEqual(ctx.exception.code, 0)

    def test_comando_con_duplicados_exit_one(self):
        self._crear_par_duplicados()
        with self.assertRaises(SystemExit) as ctx:
            call_command('resolve_duplicate_financiamientos', stdout=StringIO())
        self.assertEqual(ctx.exception.code, 1)

    def test_comando_check_solo_diagnostico(self):
        self._crear_par_duplicados()
        count_antes = Financiamiento.objects.count()
        with self.assertRaises(SystemExit) as ctx:
            call_command('resolve_duplicate_financiamientos', check=True, stdout=StringIO())
        self.assertEqual(ctx.exception.code, 1)
        self.assertEqual(Financiamiento.objects.count(), count_antes)

    def test_comando_export_no_modifica(self):
        self._crear_par_duplicados()
        count_antes = Financiamiento.objects.count()
        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp) / 'out.json'
            try:
                call_command(
                    'resolve_duplicate_financiamientos',
                    export=str(ruta),
                    stdout=StringIO(),
                )
            except SystemExit:
                pass
            self.assertEqual(Financiamiento.objects.count(), count_antes)
            self.assertTrue(ruta.exists())

    def test_check_migration_readiness_con_duplicados(self):
        self._crear_par_duplicados()
        out = StringIO()
        with self.assertRaises(SystemExit) as ctx:
            call_command('check_migration_readiness', stdout=out)
        self.assertEqual(ctx.exception.code, 1)
        self.assertIn('resolve_duplicate_financiamientos', out.getvalue())

    def test_interactive_confirmacion_invalida(self):
        self._crear_par_duplicados()
        inputs = iter(['1', 'CONFIRMAR MAL', '5'])
        with mock.patch('builtins.input', side_effect=inputs):
            call_command('resolve_duplicate_financiamientos', interactive=True, stdout=StringIO())
        self.assertTrue(venta_tiene_duplicados(self.venta.id_venta))

    def test_interactive_omitir_venta(self):
        ids = self._crear_par_duplicados()
        inputs = iter(['4'])
        with mock.patch('builtins.input', side_effect=inputs):
            call_command('resolve_duplicate_financiamientos', interactive=True, stdout=StringIO())
        self.assertEqual(Financiamiento.objects.filter(id_venta=self.venta).count(), 2)
        self.assertEqual(
            set(Financiamiento.objects.filter(id_venta=self.venta).values_list('id_financiamiento', flat=True)),
            set(ids),
        )

    @mock.patch(
        'motoshop.management.commands.resolve_duplicate_financiamientos.nuevo_archivo_auditoria'
    )
    def test_interactive_eliminar_con_confirmacion(self, mock_audit_path):
        ids = self._crear_par_duplicados()
        conservar = ids[0]
        eliminar = ids[1]
        with tempfile.TemporaryDirectory() as tmp:
            audit = Path(tmp) / 'audit.json'
            mock_audit_path.return_value = audit
            inputs = iter([
                '2',
                f'CONFIRMAR VENTA {self.venta.id_venta}',
                str(conservar),
                f'ELIMINAR FINANCIAMIENTO {eliminar}',
            ])
            with mock.patch('builtins.input', side_effect=inputs):
                call_command('resolve_duplicate_financiamientos', interactive=True, stdout=StringIO())
            self.assertEqual(Financiamiento.objects.filter(id_venta=self.venta).count(), 1)
            self.assertTrue(audit.exists())

    def test_rollback_ante_error_en_eliminacion(self):
        f1 = self._crear_fin_directo(1000, 1)
        self._crear_fin_directo(2000, 2)
        with mock.patch.object(Financiamiento, 'delete', side_effect=RuntimeError('fallo simulado')):
            with self.assertRaises(RuntimeError):
                respaldar_y_eliminar_duplicados(self.venta.id_venta, f1.id_financiamiento, 'tester')
        self.assertEqual(Financiamiento.objects.filter(id_venta=self.venta).count(), 2)

    def _crear_fin_directo(self, monto, suffix):
        return Financiamiento.objects.create(
            id_venta=self.venta, entidad_financiera=f'B{suffix}',
            monto_financiado=Decimal(str(monto)), tasa_interes=Decimal('5'),
            plazo_meses=6, cuota_mensual=Decimal('450'),
            entrada=0, saldo_pendiente=Decimal(str(monto)), estado='activo',
        )


@tag('postgres')
@override_settings(
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
)
class FinanciamientoDuplicadoPostgresTests(TransactionTestCase):
    """select_for_update con duplicados — requiere PostgreSQL."""

    def setUp(self):
        if connection.vendor != 'postgresql':
            self.skipTest('Requiere PostgreSQL (--settings=config.settings_test_postgres)')

        quitar_unique_financiamiento_por_venta()
        self.staff = User.objects.create_user('pgadm', 'pg@t.com', 'x', is_staff=True)
        self.cliente = User.objects.create_user('pgcli', 'pgc@t.com', 'x')
        cart = CarritoCompras.objects.create(id_usuario_cliente=self.cliente, estado='procesado')
        pedido = Pedido.objects.create(
            id_usuario_cliente=self.cliente, id_carrito=cart,
            total=Decimal('8000'), estado='confirmed',
        )
        self.venta = Venta.objects.create(
            id_pedido=pedido, id_usuario_cliente=self.cliente,
            id_usuario_vendedor=self.staff, total_venta=Decimal('8000'), estado='pendiente',
        )
        for i in range(2):
            Financiamiento.objects.create(
                id_venta=self.venta, entidad_financiera=f'PG{i}',
                monto_financiado=Decimal('4000'), tasa_interes=Decimal('5'),
                plazo_meses=12, cuota_mensual=Decimal('350'),
                entrada=0, saldo_pendiente=Decimal('4000'), estado='activo',
            )

    def test_cancelar_duplicados_con_select_for_update(self):
        conservar = Financiamiento.objects.filter(id_venta=self.venta).order_by('id_financiamiento').first()
        with tempfile.TemporaryDirectory() as tmp:
            audit = Path(tmp) / 'audit_pg.json'
            cancelar_duplicados(self.venta.id_venta, conservar.id_financiamiento, 'pg_tester', audit)
        cancelados = Financiamiento.objects.filter(id_venta=self.venta, estado='cancelado')
        self.assertEqual(cancelados.count(), 1)
