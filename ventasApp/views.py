from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_GET, require_http_methods

from .forms import ClienteForm, VentaForm
from .models import Cliente, Venta


@login_required
@permission_required("ventasApp.view_cliente", raise_exception=True)
@require_GET
def clientes_lista(request):
    q = request.GET.get("q", "").strip()
    clientes = Cliente.objects.all()
    if q:
        clientes = clientes.filter(Q(nombre__icontains=q) | Q(correo__icontains=q) | Q(telefono__icontains=q))
    return render(request, "clientes/lista.html", {"clientes": clientes, "q": q})


@login_required
@permission_required("ventasApp.add_cliente", raise_exception=True)
@require_http_methods(["GET", "POST"])
def clientes_crear(request):
    form = ClienteForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Cliente registrado.")
        return redirect("clientes_lista")
    return render(request, "comunes/formulario.html", {
        "titulo": "Agregar cliente", "form": form, "volver_url": reverse("clientes_lista"),
    })


@login_required
@permission_required("ventasApp.change_cliente", raise_exception=True)
@require_http_methods(["GET", "POST"])
def clientes_editar(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    form = ClienteForm(request.POST if request.method == "POST" else None, instance=cliente)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Cliente actualizado.")
        return redirect("clientes_lista")
    return render(request, "comunes/formulario.html", {
        "titulo": "Editar cliente", "form": form, "volver_url": reverse("clientes_lista"),
    })


@login_required
@permission_required("ventasApp.delete_cliente", raise_exception=True)
@require_http_methods(["GET", "POST"])
def clientes_eliminar(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == "POST":
        try:
            cliente.delete()
            messages.success(request, "Cliente eliminado.")
        except ProtectedError:
            messages.error(request, "No se puede eliminar este cliente porque tiene ventas asociadas.")
        return redirect("clientes_lista")
    return render(request, "comunes/eliminar.html", {
        "titulo": "Eliminar cliente", "objeto": cliente, "volver_url": reverse("clientes_lista"),
    })


@login_required
@permission_required("ventasApp.view_venta", raise_exception=True)
@require_GET
def ventas_lista(request):
    q = request.GET.get("q", "").strip()
    fecha = request.GET.get("fecha", "").strip()
    ventas = Venta.objects.select_related("cliente", "disco", "disco__artista")
    if q:
        ventas = ventas.filter(
            Q(cliente__nombre__icontains=q) | Q(cliente__correo__icontains=q) |
            Q(disco__titulo__icontains=q) | Q(disco__artista__nombre__icontains=q)
        )
    if fecha:
        try:
            fecha_valida = parse_date(fecha)
        except ValueError:
            fecha_valida = None
        if fecha_valida:
            ventas = ventas.filter(fecha=fecha_valida)
        else:
            messages.warning(request, "La fecha no es válida. Usa el formato año-mes-día.")
    return render(request, "ventas/lista.html", {"ventas": ventas, "q": q, "fecha": fecha})


@login_required
@permission_required("ventasApp.add_venta", raise_exception=True)
@require_http_methods(["GET", "POST"])
def ventas_crear(request):
    form = VentaForm(
        request.POST if request.method == "POST" else None,
        initial={"disco": request.GET.get("disco")},
    )
    if request.method == "POST" and form.is_valid():
        try:
            form.save()
            messages.success(request, "Venta registrada. Se descontó el stock.")
            return redirect("ventas_lista")
        except ValidationError as error:
            form.add_error(None, error)
    return render(request, "comunes/formulario.html", {
        "titulo": "Registrar venta", "form": form, "volver_url": reverse("ventas_lista"),
    })


@login_required
@permission_required("ventasApp.change_venta", raise_exception=True)
@require_http_methods(["GET", "POST"])
def ventas_editar(request, pk):
    venta = get_object_or_404(Venta, pk=pk)
    form = VentaForm(request.POST if request.method == "POST" else None, instance=venta)
    if request.method == "POST" and form.is_valid():
        try:
            form.save()
            messages.success(request, "Venta actualizada. Se ajustó el stock.")
            return redirect("ventas_lista")
        except ValidationError as error:
            form.add_error(None, error)
    return render(request, "comunes/formulario.html", {
        "titulo": "Editar venta", "form": form, "volver_url": reverse("ventas_lista"),
    })


@login_required
@permission_required("ventasApp.delete_venta", raise_exception=True)
@require_http_methods(["GET", "POST"])
def ventas_eliminar(request, pk):
    venta = get_object_or_404(Venta, pk=pk)
    if request.method == "POST":
        venta.delete()
        messages.success(request, "Venta eliminada. Se devolvieron sus unidades al stock.")
        return redirect("ventas_lista")
    return render(request, "comunes/eliminar.html", {
        "titulo": "Eliminar venta", "objeto": venta, "volver_url": reverse("ventas_lista"),
    })
