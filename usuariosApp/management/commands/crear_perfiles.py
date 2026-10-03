from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.db import transaction
from usuariosApp.perfiles import crear_grupo_cliente


class Command(BaseCommand):
    help = "Crea o actualiza los perfiles Administrador, Operador, Consulta y Cliente."

    @transaction.atomic
    def handle(self, *args, **options):
        permisos = Permission.objects.filter(
            content_type__app_label__in=["artistasApp", "discosApp", "ventasApp"]
        )
        acciones = {
            "Administrador": ["add", "change", "delete", "view"],
            "Operador": ["add", "change", "view"],
            "Consulta": ["view"],
        }
        for nombre, permitidas in acciones.items():
            grupo, _ = Group.objects.get_or_create(name=nombre)
            seleccion = [p for p in permisos if p.codename.split("_")[0] in permitidas]
            if nombre == "Administrador":
                seleccion += list(Permission.objects.filter(
                    content_type__app_label="auth", content_type__model__in=["user", "group"]
                ))
            grupo.permissions.set(seleccion)
            self.stdout.write(self.style.SUCCESS(f"Perfil {nombre}: {len(seleccion)} permisos."))
        cliente = crear_grupo_cliente()
        self.stdout.write(self.style.SUCCESS(f"Perfil Cliente: {cliente.permissions.count()} permisos."))
