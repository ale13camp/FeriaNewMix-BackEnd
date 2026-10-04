from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods

from discosApp.models import Disco
from .forms_compra import BusquedaComprasForm, CompraForm
from .models import Cliente, Venta


def cliente_del_usuario(usuario):
    cliente = Cliente.objects.filter(usuario=usuario).first()
    if cliente is None:
        raise PermissionDenied("Esta sección requiere una cuenta de cliente.")
    return cliente


@login_required
@require_GET
def compras_lista(request):
    cliente = cliente_del_usuario(request.user)
    compras = Venta.objects.filter(cliente=cliente).select_related("disco", "disco__artista")
    form = BusquedaComprasForm(request.GET)
    if form.is_valid():
        q = form.cleaned_data["q"]
        desde = form.cleaned_data["fecha_desde"]
        hasta = form.cleaned_data["fecha_hasta"]
        if q:
            compras = compras.filter(disco__titulo__icontains=q)
        if desde:
            compras = compras.filter(fecha__gte=desde)
        if hasta:
            compras = compras.filter(fecha__lte=hasta)
    else:
        compras = compras.none()
    filtros_activos = any(request.GET.get(campo, "").strip() for campo in ["q", "fecha_desde", "fecha_hasta"])
    return render(request, "compras/lista.html", {
        "compras": compras, "form": form, "filtros_activos": filtros_activos,
    })


@login_required
@require_http_methods(["GET", "POST"])
def compra_crear(request, disco_id):
    cliente = cliente_del_usuario(request.user)
    disco = get_object_or_404(Disco.objects.select_related("artista"), pk=disco_id)
    form = CompraForm(request.POST if request.method == "POST" else None, initial={"cantidad": 1})
    cantidad = 1 if request.method == "GET" else None
    if request.method == "POST" and form.is_valid():
        cantidad = form.cleaned_data["cantidad"]
        # El cliente, el disco y el precio se obtienen en el servidor.
        compra = Venta(
            cliente=cliente, disco=disco, fecha=timezone.localdate(),
            cantidad=cantidad, precio_unitario=disco.precio,
        )
        try:
            compra.save()
        except ValidationError as error:
            form.add_error(None, error.messages)
        else:
            messages.success(request, "Compra registrada. Se descontó el stock.")
            return redirect("compras_lista")
    total = disco.precio * cantidad if cantidad is not None else None
    return render(request, "compras/confirmar.html", {
        "disco": disco, "form": form, "total": total, "cantidad_total": cantidad,
    })
