from django.contrib.auth.models import Group, Permission


def crear_grupo_cliente():
    grupo, _ = Group.objects.get_or_create(name="Cliente")
    permisos = Permission.objects.filter(
        content_type__app_label__in=["artistasApp", "discosApp"],
        codename__in=["view_artista", "view_disco"],
    )
    grupo.permissions.set(permisos)
    return grupo
