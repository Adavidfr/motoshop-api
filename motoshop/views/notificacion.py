# motoshop/views/notificacion.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from django.contrib.auth.models import User
from motoshop.models import Notificacion
from motoshop.serializers.notificacion import NotificacionSerializer, NotificacionCreateSerializer
from motoshop.pagination import StandardPagination
from motoshop.filters import NotificacionFilter
from motoshop.utils.emails import send_notification_email, send_mass_notification_emails


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

    def perform_create(self, serializer):
        """Sobreescribimos para enviar el correo al crear una notificación individual."""
        notificacion = serializer.save()
        if notificacion.id_usuario and notificacion.id_usuario.email:
            send_notification_email(
                notificacion.id_usuario, 
                notificacion.titulo, 
                notificacion.mensaje
            )

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

    @action(detail=False, methods=['post'], url_path='enviar_masivo', permission_classes=[IsAdminUser])
    def enviar_masivo(self, request):
        """
        Crea notificaciones y envía correos a todos los usuarios o a una lista específica.
        Body esperado:
        {
            "titulo": "Asunto del correo",
            "mensaje": "Cuerpo del correo",
            "usuarios": [1, 2, 3] # Opcional, si no se envía va a todos.
        }
        """
        titulo = request.data.get('titulo')
        mensaje = request.data.get('mensaje')
        user_ids = request.data.get('usuarios')

        if not titulo or not mensaje:
            return Response({'error': 'titulo y mensaje son requeridos.'}, status=status.HTTP_400_BAD_REQUEST)

        if user_ids:
            users = User.objects.filter(id__in=user_ids)
        else:
            users = User.objects.all()

        if not users.exists():
            return Response({'error': 'No se encontraron usuarios a los que enviar.'}, status=status.HTTP_404_NOT_FOUND)

        # Crear registros en base de datos
        notificaciones = [
            Notificacion(id_usuario=user, titulo=titulo, mensaje=mensaje)
            for user in users
        ]
        Notificacion.objects.bulk_create(notificaciones)

        # Enviar correos masivos
        send_mass_notification_emails(users, titulo, mensaje)

        return Response({
            'detail': f'Notificación creada y correos enviados a {users.count()} usuarios.'
        }, status=status.HTTP_201_CREATED)
