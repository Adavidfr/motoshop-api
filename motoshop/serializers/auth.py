from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView


def get_user_role(user) -> str:
    """Devuelve el nombre del primer grupo del usuario o 'usuario' por defecto."""
    group = user.groups.first()
    return group.name if group else 'usuario'


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