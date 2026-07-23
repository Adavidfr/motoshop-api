"""
Datos mínimos de desarrollo (idempotente).

Uso:
  set SEED_DEV_PASSWORD=tu_contraseña_segura
  python manage.py seed_dev_data

Si SEED_DEV_PASSWORD no está definida, se genera una contraseña aleatoria
y se muestra una sola vez en consola (no se guarda en archivos).
"""

import getpass
import secrets

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from decouple import config

from motoshop.models import ClientePerfil
from motoshop.models.categoria_moto import CategoriaMoto
from motoshop.models.marca import Marca
from motoshop.models.moto import Moto
from motoshop.models.proveedor import Proveedor
from motoshop.models.repuesto import Repuesto
from motoshop.models.servicio import Servicio


class Command(BaseCommand):
    help = 'Crea datos mínimos de desarrollo de forma idempotente (get_or_create).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--admin-username',
            default=config('SEED_ADMIN_USERNAME', default='admin_dev'),
            help='Username del administrador (default: admin_dev o SEED_ADMIN_USERNAME).',
        )
        parser.add_argument(
            '--client-username',
            default=config('SEED_CLIENT_USERNAME', default='cliente_dev'),
            help='Username del cliente (default: cliente_dev o SEED_CLIENT_USERNAME).',
        )

    def handle(self, *args, **options):
        password = config('SEED_DEV_PASSWORD', default='')
        generated = False
        if not password:
            password = secrets.token_urlsafe(16)
            generated = True

        admin_username = options['admin_username']
        client_username = options['client_username']

        admin, admin_created = User.objects.get_or_create(
            username=admin_username,
            defaults={
                'email': f'{admin_username}@dev.local',
                'is_staff': True,
                'is_superuser': True,
            },
        )
        if admin_created or not admin.has_usable_password():
            admin.set_password(password)
            admin.is_staff = True
            admin.is_superuser = True
            admin.save()

        cliente, cliente_created = User.objects.get_or_create(
            username=client_username,
            defaults={
                'email': f'{client_username}@dev.local',
                'is_staff': False,
            },
        )
        if cliente_created or not cliente.has_usable_password():
            cliente.set_password(password)
            cliente.save()

        perfil, perfil_created = ClientePerfil.objects.get_or_create(
            id_usuario=cliente,
            defaults={
                'cedula': '1000000001',
                'telefono': '0990000001',
                'direccion': 'Av. Dev 123',
            },
        )
        if not perfil_created:
            ClientePerfil.objects.filter(pk=perfil.pk).update(
                telefono='0990000001',
                direccion='Av. Dev 123',
            )

        marca, _ = Marca.objects.get_or_create(
            nombre='Marca Dev',
            defaults={'estado': True},
        )
        categoria, _ = CategoriaMoto.objects.get_or_create(
            nombre='Categoria Dev',
            defaults={'estado': True},
        )
        moto, _ = Moto.objects.update_or_create(
            modelo='Moto Dev 2024',
            marca=marca,
            defaults={
                'categoria': categoria,
                'anio': 2024,
                'cilindraje': 250,
                'color': 'Negro',
                'precio': '8500.00',
                'stock': 5,
                'estado': 'disponible',
            },
        )
        repuesto, _ = Repuesto.objects.update_or_create(
            sku='REP-DEV-001',
            defaults={
                'nombre': 'Repuesto Dev',
                'descripcion': 'Repuesto de prueba',
                'costo': '10.00',
                'precio_venta': '18.00',
                'stock': 20,
                'estado': 'disponible',
            },
        )
        proveedor, _ = Proveedor.objects.get_or_create(
            nombre='Proveedor Dev',
            defaults={
                'contacto': '0990000002',
                'correo': 'proveedor@dev.local',
                'estado': True,
            },
        )
        servicio, _ = Servicio.objects.get_or_create(
            nombre='Servicio Taller Dev',
            defaults={
                'descripcion': 'Mantenimiento de prueba',
                'precio_base': '45.00',
                'tiempo_estimado_minutos': 60,
                'estado': True,
            },
        )

        self.stdout.write(self.style.SUCCESS('Datos de desarrollo listos (idempotente).'))
        self.stdout.write(f'  Admin:    {admin_username} (staff=True, superuser=True)')
        self.stdout.write(f'  Cliente:  {client_username}')
        self.stdout.write(f'  Perfil:   cedula={perfil.cedula}')
        self.stdout.write(f'  Marca:    {marca.nombre} (id={marca.pk})')
        self.stdout.write(f'  Categoría:{categoria.nombre} (id={categoria.pk})')
        self.stdout.write(f'  Moto:     {moto.modelo} (id={moto.id_moto}, stock={moto.stock})')
        self.stdout.write(f'  Repuesto: {repuesto.sku} (id={repuesto.id_repuesto})')
        self.stdout.write(f'  Proveedor:{proveedor.nombre} (id={proveedor.pk})')
        self.stdout.write(f'  Servicio: {servicio.nombre} (id={servicio.pk})')

        if generated:
            self.stdout.write(self.style.WARNING(
                '\nSEED_DEV_PASSWORD no estaba definida. Contraseña generada (guárdela):'
            ))
            self.stdout.write(f'  Usuario admin/cliente: *** ({len(password)} caracteres)')
            self.stdout.write(
                '  Defina SEED_DEV_PASSWORD en el entorno para reutilizar la misma contraseña.'
            )
        else:
            self.stdout.write(
                f'\nContraseña aplicada desde SEED_DEV_PASSWORD (usuario: {getpass.getuser()}).'
            )
