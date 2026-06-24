from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User


class UserWithRoleAdmin(BaseUserAdmin):
    """
    Extiende el panel de admin para mostrar el rol del usuario.
    """
    list_display = ('username', 'email', 'get_role', 'is_staff', 'is_active', 'date_joined')
    list_filter  = ('groups', 'is_staff', 'is_active')

    @admin.display(description='Rol')
    def get_role(self, obj):
        group = obj.groups.first()
        return group.name if group else '—'


admin.site.unregister(User)
admin.site.register(User, UserWithRoleAdmin)
