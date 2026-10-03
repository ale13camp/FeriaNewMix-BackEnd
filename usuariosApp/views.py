from django.contrib import messages
from django.contrib.auth import login
from django.db import transaction
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from ventasApp.models import Cliente
from .forms import RegistroClienteForm
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
