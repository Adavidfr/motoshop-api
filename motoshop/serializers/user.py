from rest_framework import serializers
from django.contrib.auth.models import User, Group

from motoshop.apps import ROLES


class RegisterSerializer(serializers.Serializer):
    username  = serializers.CharField(max_length=150)
    email     = serializers.EmailField()
    password  = serializers.CharField(min_length=8, write_only=True)
    password2 = serializers.CharField(write_only=True)
    role      = serializers.ChoiceField(choices=ROLES, default='usuario')

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('This username is already taken.')
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('This email is already registered.')
        return value

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({'password2': 'Passwords do not match.'})
        return data

    def create(self, validated_data):
        role = validated_data.pop('role', 'usuario')
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        group, _ = Group.objects.get_or_create(name=role)
        user.groups.add(group)
        return user


class UserSerializer(serializers.ModelSerializer):
    """
    Vista completa del usuario para staff.
    num_orders agregado en Etapa 5 con el modelo Pedido disponible.
    """
    role       = serializers.SerializerMethodField()
    num_orders = serializers.SerializerMethodField()

    class Meta:
        model  = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'is_staff', 'is_active', 'date_joined', 'role', 'num_orders',
        ]
        read_only_fields = ['id', 'date_joined']

    def get_role(self, obj):
        group = obj.groups.first()
        return group.name if group else 'usuario'

    def get_num_orders(self, obj):
        return obj.orders.count()


class UserProfileSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()

    class Meta:
        model  = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role']
        read_only_fields = ['id', 'role']

    def get_role(self, obj):
        group = obj.groups.first()
        return group.name if group else 'usuario'

    def validate_email(self, value):
        request = self.context.get('request')
        if User.objects.filter(email=value).exclude(pk=request.user.pk).exists():
            raise serializers.ValidationError('This email is already in use.')
        return value


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password     = serializers.CharField(min_length=8, write_only=True)
    new_password2    = serializers.CharField(write_only=True)

    def validate_current_password(self, value):
        if not self.context['request'].user.check_password(value):
            raise serializers.ValidationError('Current password is incorrect.')
        return value

    def validate(self, data):
        if data['new_password'] != data['new_password2']:
            raise serializers.ValidationError({'new_password2': 'Passwords do not match.'})
        return data