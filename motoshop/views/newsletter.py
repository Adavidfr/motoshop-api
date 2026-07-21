from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from motoshop.utils.emails import send_newsletter_invitation

class NewsletterSubscribeView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        
        if not email:
            return Response({'error': 'El correo electrónico es requerido.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Enviar correo de invitación
        send_newsletter_invitation(email)
        
        return Response({'message': '¡Suscripción exitosa! Revisa tu correo.'}, status=status.HTTP_200_OK)
