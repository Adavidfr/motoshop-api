from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView


def get_user_role(user) -> str:
    """Devuelve el rol funcional derivado de privilegios administrativos."""
    if user.is_superuser or user.is_staff:
        return 'administrador'
    return 'cliente'


class CustomTokenSerializer(TokenObtainPairSerializer):

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        token['email']    = user.email
        token['is_staff'] = user.is_staff
        token['role']     = get_user_role(user)
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data['user_id']  = self.user.id
        data['username'] = self.user.username
        data['email']    = self.user.email
        data['is_staff'] = self.user.is_staff
        data['role']     = get_user_role(self.user)
        return data


class CustomTokenView(TokenObtainPairView):
    serializer_class = CustomTokenSerializer