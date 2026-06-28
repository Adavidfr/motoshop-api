# motoshop/views/notificacion.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from motoshop.models import Notificacion
from motoshop.serializers.notificacion import NotificacionSerializer, NotificacionCreateSerializer
from motoshop.pagination import StandardPagination
from motoshop.filters import NotificacionFilter


class NotificacionViewSet(viewsets.ModelViewSet):
    """
    ViewSet CRUD de notificaciones.

    Endpoints generados:
      GET    /notificaciones/              → listar (admin: todas; usuario: las propias)
      POST   /notificaciones/              → crear (solo admin)
      GET    /notificaciones/<id>/         → detalle
      PATCH  /notificaciones/<id>/         → editar
      DELETE /notificaciones/<id>/         → eliminar

    Acciones custom:
      POST /notificaciones/<id>/marcar_leida/   → marca como leída
      POST /notificaciones/marcar_todas_leidas/ → marca todas como leídas
    """
    pagination_class  = StandardPagination
    filter_backends   = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class   = NotificacionFilter
    search_fields     = ['titulo', 'mensaje']
    ordering_fields   = ['id_notificacion', 'fecha_creacion']
    ordering          = ['-fecha_creacion']
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_permissions(self):
        if self.action == 'create':
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        qs   = Notificacion.objects.select_related('id_usuario').all()
        if not user.is_staff:
            qs = qs.filter(id_usuario=user)
        return qs

    def get_serializer_class(self):
        if self.action == 'create':
            return NotificacionCreateSerializer
        return NotificacionSerializer

    # ------------------------------------------------------------------ #
    #  Actions custom                                                       #
    # ------------------------------------------------------------------ #
    @action(detail=True, methods=['post'], url_path='marcar_leida')
    def marcar_leida(self, request, pk=None):
        """Marca una notificación como leída."""
        notificacion = self.get_object()
        notificacion.leido = True
        notificacion.save(update_fields=['leido'])
        return Response({'detail': 'Notificación marcada como leída.'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='marcar_todas_leidas')
    def marcar_todas_leidas(self, request):
        """Marca todas las notificaciones del usuario como leídas."""
        updated = self.get_queryset().filter(leido=False).update(leido=True)
        return Response({'detail': f'{updated} notificaciones marcadas como leídas.'}, status=status.HTTP_200_OK)
