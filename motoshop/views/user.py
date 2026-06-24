from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth.models import User, Group

from motoshop.serializers.user import (
    UserSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer,
)
from motoshop.pagination import StandardPagination
from motoshop.apps import ROLES


class UserViewSet(viewsets.ModelViewSet):
    queryset           = User.objects.all().order_by('id')
    serializer_class   = UserSerializer
    permission_classes = [IsAdminUser]
    pagination_class   = StandardPagination
    filter_backends    = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields   = ['is_staff', 'is_active']
    search_fields      = ['username', 'email', 'first_name', 'last_name']
    ordering_fields    = ['id', 'username', 'date_joined']
    ordering           = ['id']

    def get_queryset(self):
        qs = super().get_queryset()
        role = self.request.query_params.get('role')
        if role:
            qs = qs.filter(groups__name=role)
        return qs

    @action(
        detail=False,
        methods=['get', 'patch'],
        permission_classes=[IsAuthenticated],
        url_path='profile',
    )
    def profile(self, request):
        if request.method == 'GET':
            return Response(
                UserProfileSerializer(request.user, context={'request': request}).data
            )
        serializer = UserProfileSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['post'],
        permission_classes=[IsAuthenticated],
        url_path='change-password',
    )
    def change_password(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response({'message': 'Password updated. Please log in again.'})

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAdminUser],
        url_path='toggle-active',
    )
    def toggle_active(self, request, pk=None):
        user = self.get_object()
        user.is_active = not user.is_active
        user.save(update_fields=['is_active'])
        state = 'activated' if user.is_active else 'deactivated'
        return Response({'message': f'User {state}.', 'is_active': user.is_active})

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAdminUser],
        url_path='stats',
    )
    def stats(self, request):
        qs = User.objects.all()
        role_counts = {
            role: qs.filter(groups__name=role).count()
            for role in ROLES
        }
        return Response({
            'total':    qs.count(),
            'active':   qs.filter(is_active=True).count(),
            'inactive': qs.filter(is_active=False).count(),
            'staff':    qs.filter(is_staff=True).count(),
            'by_role':  role_counts,
        })

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAdminUser],
        url_path='set-role',
    )
    def set_role(self, request, pk=None):
        """Cambia el rol (grupo) de un usuario. Solo admins."""
        user = self.get_object()
        new_role = request.data.get('role')
        if new_role not in ROLES:
            return Response(
                {'error': f'Rol inválido. Opciones: {", ".join(ROLES)}'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.groups.clear()
        group, _ = Group.objects.get_or_create(name=new_role)
        user.groups.add(group)
        return Response({'message': f'Rol actualizado a "{new_role}".', 'role': new_role})