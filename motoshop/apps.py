from django.apps import AppConfig


ROLES = ['admin', 'usuario', 'cliente', 'vendedor']


class MotoshopConfig(AppConfig):
    name = 'motoshop'

    def ready(self):
        from django.db.models.signals import post_migrate
        post_migrate.connect(_create_roles, sender=self)


def _create_roles(sender, **kwargs):
    """Crea los grupos de roles si no existen (idempotente)."""
    from django.contrib.auth.models import Group
    for role in ROLES:
        Group.objects.get_or_create(name=role)
