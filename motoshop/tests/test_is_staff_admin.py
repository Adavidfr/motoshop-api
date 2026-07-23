from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from motoshop.models.categoria_moto import CategoriaMoto
from motoshop.models.marca import Marca
from motoshop.serializers.user import UserProfileSerializer, UserSerializer


class IsStaffAdminPermissionsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.marca = Marca.objects.create(nombre='Yamaha', estado=True)
        self.categoria = CategoriaMoto.objects.create(nombre='Deportiva', estado=True)
        self.moto_payload = {
            'categoria': self.categoria.id_categoria,
            'marca': self.marca.id_marca,
            'modelo': 'R15',
            'anio': 2024,
            'cilindraje': 155,
            'color': 'Azul',
            'precio': '4500.00',
            'stock': 5,
            'estado': 'disponible',
        }

        self.staff_user = User.objects.create_user(
            username='staff1',
            email='staff1@example.com',
            password='password123',
            is_staff=True,
        )
        self.client_user = User.objects.create_user(
            username='cliente1',
            email='cliente1@example.com',
            password='password123',
            is_staff=False,
        )

    def test_anonymous_can_list_motos(self):
        response = self.client.get('/api/motos/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_staff_without_group_can_create_moto(self):
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.post('/api/motos/', self.moto_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_client_cannot_create_moto(self):
        self.client.force_authenticate(user=self.client_user)
        response = self.client.post('/api/motos/', self.moto_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_login_returns_administrador_role(self):
        response = self.client.post('/api/auth/login/', {
            'username': 'staff1',
            'password': 'password123',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_staff'])
        self.assertEqual(response.data['role'], 'administrador')

    def test_client_login_returns_cliente_role(self):
        response = self.client.post('/api/auth/login/', {
            'username': 'cliente1',
            'password': 'password123',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_staff'])
        self.assertEqual(response.data['role'], 'cliente')


class UserRoleSerializationTests(TestCase):
    def test_user_serializer_uses_functional_role(self):
        staff = User.objects.create_user(
            username='admin1',
            email='admin1@example.com',
            password='password123',
            is_staff=True,
        )
        client = User.objects.create_user(
            username='buyer1',
            email='buyer1@example.com',
            password='password123',
            is_staff=False,
        )

        self.assertEqual(UserSerializer(staff).data['role'], 'administrador')
        self.assertEqual(UserSerializer(client).data['role'], 'cliente')
        self.assertEqual(UserProfileSerializer(staff).data['role'], 'administrador')
        self.assertEqual(UserProfileSerializer(client).data['role'], 'cliente')


class UserViewSetFunctionalRoleTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            username='admin2',
            email='admin2@example.com',
            password='password123',
            is_staff=True,
        )
        self.client.force_authenticate(user=self.admin)

    def test_stats_returns_functional_roles(self):
        User.objects.create_user(
            username='buyer2',
            email='buyer2@example.com',
            password='password123',
            is_staff=False,
        )
        response = self.client.get('/api/users/stats/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['by_role']['administrador'], 1)
        self.assertEqual(response.data['by_role']['cliente'], 1)

    def test_set_role_endpoint_is_deprecated(self):
        target = User.objects.create_user(
            username='buyer3',
            email='buyer3@example.com',
            password='password123',
            is_staff=False,
        )
        response = self.client.post(
            f'/api/users/{target.id}/set-role/',
            {'role': 'admin'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_410_GONE)
        self.assertIn('deprecado', response.data['error'])

    def test_filter_users_by_functional_role(self):
        User.objects.create_user(
            username='buyer4',
            email='buyer4@example.com',
            password='password123',
            is_staff=False,
        )
        admins = self.client.get('/api/users/?role=administrador')
        clients = self.client.get('/api/users/?role=cliente')

        self.assertEqual(admins.status_code, status.HTTP_200_OK)
        self.assertEqual(clients.status_code, status.HTTP_200_OK)
        self.assertEqual(len(admins.data['results']), 1)
        self.assertEqual(len(clients.data['results']), 1)
