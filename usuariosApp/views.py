from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from ventasApp.models import Cliente
from .forms import CambiarPasswordForm, PerfilClienteForm, RegistroClienteForm
from .perfiles import crear_grupo_cliente


@require_http_methods(["GET", "POST"])
def registro(request):
    if request.user.is_authenticated:
        return redirect("home")
    form = RegistroClienteForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        # La cuenta y los datos del cliente se guardan juntos.
        with transaction.atomic():
            usuario = form.save()
            Cliente.objects.create(
                usuario=usuario, nombre=form.cleaned_data["nombre"],
                correo=form.cleaned_data["correo"], telefono=form.cleaned_data["telefono"],
            )
            usuario.groups.add(crear_grupo_cliente())
        login(request, usuario)
        messages.success(request, "Tu cuenta de cliente fue creada correctamente.")
        return redirect("home")
    return render(request, "registration/registro.html", {"form": form})


def _cliente_actual(request):
    cliente = Cliente.objects.filter(usuario=request.user).first()
    if cliente is None:
        raise PermissionDenied
    return cliente


@login_required
@require_http_methods(["GET", "POST"])
def mi_perfil(request):
    cliente = _cliente_actual(request)
    form = PerfilClienteForm(request.POST if request.method == "POST" else None, instance=cliente)
    if request.method == "POST" and form.is_valid():
        # Se actualiza únicamente el cliente de esta cuenta y sus datos de usuario.
        with transaction.atomic():
            cliente = form.save()
            request.user.first_name = cliente.nombre
            request.user.email = cliente.correo
            request.user.save(update_fields=["first_name", "email"])
        messages.success(request, "Tu perfil fue actualizado correctamente.")
        return redirect("mi_perfil")
    return render(request, "usuarios/perfil.html", {"form": form})


@login_required
@require_http_methods(["GET", "POST"])
def cambiar_password(request):
    _cliente_actual(request)
    form = CambiarPasswordForm(request.user, request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        usuario = form.save()
        update_session_auth_hash(request, usuario)
        messages.success(request, "Tu contraseña fue cambiada correctamente.")
        return redirect("mi_perfil")
    return render(request, "registration/cambiar_password.html", {"form": form})
