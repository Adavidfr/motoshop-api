from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from motoshop.models import ClientePerfil


class RegisterPublicClientTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    @patch('motoshop.views.auth.send_welcome_email')
    def test_register_without_role_creates_client_user(self, _mock_email):
        response = self.client.post('/api/auth/register/', {
            'username': 'cliente1',
            'email': 'cliente1@example.com',
            'password': 'password123',
            'password2': 'password123',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(response.data['is_staff'])
        self.assertEqual(response.data['role'], 'cliente')
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

        user = User.objects.get(username='cliente1')
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertEqual(user.groups.count(), 0)
        self.assertFalse(ClientePerfil.objects.filter(id_usuario=user).exists())

    @patch('motoshop.views.auth.send_welcome_email')
    def test_register_with_role_is_rejected(self, _mock_email):
        response = self.client.post('/api/auth/register/', {
            'username': 'cliente2',
            'email': 'cliente2@example.com',
            'password': 'password123',
            'password2': 'password123',
            'role': 'admin',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('role', response.data)
        self.assertFalse(User.objects.filter(username='cliente2').exists())

    @patch('motoshop.views.auth.send_welcome_email')
    def test_registered_user_has_no_profile_until_created(self, _mock_email):
        register = self.client.post('/api/auth/register/', {
            'username': 'cliente3',
            'email': 'cliente3@example.com',
            'password': 'password123',
            'password2': 'password123',
        }, format='json')
        self.assertEqual(register.status_code, status.HTTP_201_CREATED)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {register.data['access']}")
        profile = self.client.get('/api/clientes/perfil/')

        self.assertEqual(profile.status_code, status.HTTP_404_NOT_FOUND)
