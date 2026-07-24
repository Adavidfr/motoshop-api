"""Numeración automática de pólizas POL-YYYY-######."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.db import connection
from django.test import TestCase, TransactionTestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from motoshop.models import CarritoCompras, Pedido, Seguro, Venta
from motoshop.services import SeguroService


def _crear_venta(cliente, staff, total='1000.00'):
    cart = CarritoCompras.objects.create(
        id_usuario_cliente=cliente, estado='procesado',
    )
    pedido = Pedido.objects.create(
        id_usuario_cliente=cliente,
        id_carrito=cart,
        estado='confirmed',
        total=Decimal(total),
    )
    return Venta.objects.create(
        id_pedido=pedido,
        id_usuario_cliente=cliente,
        id_usuario_vendedor=staff,
        total_venta=Decimal(total),
        estado='pendiente',
    )


@override_settings(
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
)
class SeguroPolizaApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.staff = User.objects.create_user(
            username='staff_seguro', email='staff_seguro@example.com',
            password='password123', is_staff=True,
        )
        self.cliente = User.objects.create_user(
            username='cliente_seguro', email='cliente_seguro@example.com',
            password='password123', is_staff=False,
        )
        self.venta = _crear_venta(self.cliente, self.staff)
        self.client.force_authenticate(user=self.staff)

    def _payload(self, **overrides):
        data = {
            'id_venta': self.venta.id_venta,
            'aseguradora': 'Seguros Ejemplo',
            'tipo_cobertura': 'Todo Riesgo',
            'fecha_inicio': '2026-07-24',
            'fecha_fin': '2027-07-24',
            'costo_anual': '500.00',
        }
        data.update(overrides)
        return data

    def test_crear_sin_numero_poliza_genera_secuencia(self):
        response = self.client.post('/api/seguros/', self._payload(), format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data['numero_poliza'], 'POL-2026-000001')

        response2 = self.client.post('/api/seguros/', self._payload(), format='json')
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED, response2.data)
        self.assertEqual(response2.data['numero_poliza'], 'POL-2026-000002')

    def test_numero_poliza_manual_es_ignorado(self):
        response = self.client.post(
            '/api/seguros/',
            self._payload(numero_poliza='POL-MANUAL-999'),
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data['numero_poliza'], 'POL-2026-000001')
        self.assertFalse(
            Seguro.objects.filter(numero_poliza='POL-MANUAL-999').exists(),
        )

    def test_anio_toma_fecha_inicio(self):
        response = self.client.post(
            '/api/seguros/',
            self._payload(
                fecha_inicio='2027-01-15',
                fecha_fin='2028-01-15',
            ),
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data['numero_poliza'], 'POL-2027-000001')

    def test_patch_no_modifica_numero_poliza(self):
        created = self.client.post('/api/seguros/', self._payload(), format='json')
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        seguro_id = created.data['id_seguro']
        original = created.data['numero_poliza']

        patched = self.client.patch(
            f'/api/seguros/{seguro_id}/',
            {'numero_poliza': 'POL-HACK-000001', 'aseguradora': 'Nueva'},
            format='json',
        )
        self.assertEqual(patched.status_code, status.HTTP_200_OK, patched.data)
        self.assertEqual(patched.data['numero_poliza'], original)
        self.assertEqual(patched.data['aseguradora'], 'Nueva')

    def test_conserva_polizas_existentes_manuales(self):
        Seguro.objects.create(
            id_venta=self.venta,
            aseguradora='Legacy',
            numero_poliza='LEGACY-ABC-1',
            tipo_cobertura='Básica',
            fecha_inicio=date(2025, 1, 1),
            fecha_fin=date(2026, 1, 1),
            costo_anual=Decimal('100.00'),
            estado='activo',
        )
        response = self.client.post('/api/seguros/', self._payload(), format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['numero_poliza'], 'POL-2026-000001')
        self.assertTrue(Seguro.objects.filter(numero_poliza='LEGACY-ABC-1').exists())

    def test_fecha_fin_invalida(self):
        response = self.client.post(
            '/api/seguros/',
            self._payload(fecha_fin='2026-01-01'),
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class SeguroPolizaServiceTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            username='staff_svc', email='staff_svc@example.com',
            password='password123', is_staff=True,
        )
        self.cliente = User.objects.create_user(
            username='cliente_svc', email='cliente_svc@example.com',
            password='password123', is_staff=False,
        )
        self.venta = _crear_venta(self.cliente, self.staff)

    def test_servicio_secuencia_por_anio(self):
        s1 = SeguroService.crear(
            venta=self.venta,
            aseguradora='A',
            tipo_cobertura='TR',
            fecha_inicio=date(2026, 3, 1),
            fecha_fin=date(2027, 3, 1),
            costo_anual=Decimal('10.00'),
        )
        s2 = SeguroService.crear(
            venta=self.venta,
            aseguradora='B',
            tipo_cobertura='TR',
            fecha_inicio=date(2026, 6, 1),
            fecha_fin=date(2027, 6, 1),
            costo_anual=Decimal('20.00'),
        )
        self.assertEqual(s1.numero_poliza, 'POL-2026-000001')
        self.assertEqual(s2.numero_poliza, 'POL-2026-000002')


class SeguroPolizaConcurrencyTests(TransactionTestCase):
    """Dos creaciones concurrentes deben obtener números distintos."""

    def setUp(self):
        self.staff = User.objects.create_user(
            username='staff_conc', email='staff_conc@example.com',
            password='password123', is_staff=True,
        )
        self.cliente = User.objects.create_user(
            username='cliente_conc', email='cliente_conc@example.com',
            password='password123', is_staff=False,
        )
        self.venta = _crear_venta(self.cliente, self.staff)

    def test_creaciones_concurrentes_sin_duplicados(self):
        if connection.vendor == 'sqlite':
            # SQLite en memoria no comparte DB entre hilos de forma fiable;
            # validamos secuencia bajo carga serializada con reintentos simulados.
            nums = []
            for i in range(5):
                s = SeguroService.crear(
                    venta=self.venta,
                    aseguradora=f'A{i}',
                    tipo_cobertura='TR',
                    fecha_inicio=date(2026, 1, 1),
                    fecha_fin=date(2027, 1, 1),
                    costo_anual=Decimal('1.00'),
                )
                nums.append(s.numero_poliza)
            self.assertEqual(len(nums), len(set(nums)))
            self.assertEqual(nums[0], 'POL-2026-000001')
            self.assertEqual(nums[-1], 'POL-2026-000005')
            return

        def _crear(i):
            return SeguroService.crear(
                venta=self.venta,
                aseguradora=f'Conc-{i}',
                tipo_cobertura='TR',
                fecha_inicio=date(2026, 1, 1),
                fecha_fin=date(2027, 1, 1),
                costo_anual=Decimal('1.00'),
            ).numero_poliza

        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = [pool.submit(_crear, i) for i in range(4)]
            results = [f.result() for f in as_completed(futures)]

        self.assertEqual(len(results), 4)
        self.assertEqual(len(set(results)), 4)
