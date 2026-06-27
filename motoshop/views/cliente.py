# motoshop/views/cliente.py
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from motoshop.models import ClientePerfil
from motoshop.serializers.cliente import ClientePerfilSerializer
from motoshop.pagination import StandardPagination


class ClientePerfilView(APIView):
    """
    GET    /clientes/perfil/  → Ver el perfil del cliente autenticado
    POST   /clientes/perfil/  → Crear el perfil del cliente autenticado
    PATCH  /clientes/perfil/  → Actualizar parcialmente el perfil del cliente autenticado
    DELETE /clientes/perfil/  → Eliminar el perfil del cliente autenticado
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            perfil = request.user.perfil_cliente
        except ClientePerfil.DoesNotExist:
            return Response(
                {'detail': 'Perfil no encontrado. Créalo con POST.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(ClientePerfilSerializer(perfil).data)

    def post(self, request):
        """Crea el perfil si no existe, o lo actualiza si ya existe (upsert)."""
        try:
            perfil     = request.user.perfil_cliente
            serializer = ClientePerfilSerializer(perfil, data=request.data, partial=True)
        except ClientePerfil.DoesNotExist:
            serializer = ClientePerfilSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save(id_usuario=request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        """Actualiza parcialmente el perfil del cliente autenticado."""
        try:
            perfil = request.user.perfil_cliente
        except ClientePerfil.DoesNotExist:
            return Response(
                {'detail': 'Perfil no encontrado. Créalo con POST.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = ClientePerfilSerializer(perfil, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request):
        """Elimina el perfil del cliente autenticado."""
        try:
            perfil = request.user.perfil_cliente
        except ClientePerfil.DoesNotExist:
            return Response(
                {'detail': 'Perfil no encontrado.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        perfil.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ClientePerfilAdminListView(generics.ListAPIView):
    """GET /clientes/ → Listar todos los perfiles (solo staff)"""
    queryset           = ClientePerfil.objects.select_related('id_usuario').all()
    serializer_class   = ClientePerfilSerializer
    permission_classes = [IsAdminUser]
    pagination_class   = StandardPagination
