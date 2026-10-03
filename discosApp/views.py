from pathlib import Path

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from artistasApp.models import Artista
from discosApp.forms import DiscoForm
from discosApp.models import Disco


@login_required
@permission_required("discosApp.view_disco", raise_exception=True)
def inicio(request):
    discos = Disco.objects.select_related("artista")
    return render(request, "discos/inicio.html", {
        "total_discos": discos.count(),
        "formatos": discos.order_by("formato").values_list("formato", flat=True).distinct(),
        "destacados": discos.filter(stock__gt=0).order_by("stock", "titulo")[:3],
    })


def filtrar_discos(request):
    discos = Disco.objects.select_related("artista")
    q = request.GET.get("q", "").strip()
    genero = request.GET.get("genero", "")
    formato = request.GET.get("formato", "")
    artista = request.GET.get("artista", "")
    if q:
        discos = discos.filter(Q(titulo__icontains=q) | Q(artista__nombre__icontains=q))
    if genero:
        discos = discos.filter(genero=genero)
    if formato:
        discos = discos.filter(formato=formato)
    if artista:
        discos = discos.filter(artista__nombre=artista)
    return {
        "discos": discos,
        "generos": Disco.objects.order_by("genero").values_list("genero", flat=True).distinct(),
        "formatos": Disco.objects.order_by("formato").values_list("formato", flat=True).distinct(),
        "artistas": Artista.objects.all(),
        "q": q, "genero_filtro": genero, "formato_filtro": formato,
        "artista_filtro": artista, "total": discos.count(),
    }


@login_required
@permission_required("discosApp.view_disco", raise_exception=True)
def catalogo(request):
    return render(request, "discos/catalogo.html", filtrar_discos(request))


@login_required
@permission_required("discosApp.view_disco", raise_exception=True)
def detalle(request, disco_id):
    disco = get_object_or_404(Disco.objects.select_related("artista"), pk=disco_id)
    return render(request, "discos/detalle.html", {
        "disco": disco,
        "otros_del_artista": Disco.objects.filter(artista=disco.artista).exclude(pk=disco.pk),
        "disponibilidad": "Disponible" if disco.stock else "Agotado",
    })


@login_required
@permission_required("discosApp.view_disco", raise_exception=True)
def lista(request):
    return render(request, "discos/lista.html", filtrar_discos(request))


@login_required
@permission_required("discosApp.add_disco", raise_exception=True)
def crear(request):
    form = DiscoForm(request.POST if request.method == "POST" else None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Disco creado.")
        return redirect("discos_lista")
    return render(request, "comunes/formulario.html", {
        "titulo": "Agregar disco", "form": form, "volver_url": reverse("discos_lista"),
    })


@login_required
@permission_required("discosApp.change_disco", raise_exception=True)
def editar(request, disco_id):
    disco = get_object_or_404(Disco, pk=disco_id)
    form = DiscoForm(request.POST if request.method == "POST" else None, request.FILES or None, instance=disco)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Disco actualizado.")
        return redirect("discos_lista")
    return render(request, "comunes/formulario.html", {
        "titulo": "Editar disco", "form": form, "volver_url": reverse("discos_lista"),
    })


@login_required
@permission_required("discosApp.delete_disco", raise_exception=True)
def eliminar(request, disco_id):
    disco = get_object_or_404(Disco, pk=disco_id)
    if request.method == "POST":
        try:
            disco.delete()
            messages.success(request, "Disco eliminado.")
        except ProtectedError:
            messages.error(request, "No se puede eliminar el disco porque tiene ventas asociadas.")
        return redirect("discos_lista")
    return render(request, "comunes/eliminar.html", {
        "titulo": "Eliminar disco", "objeto": disco, "volver_url": reverse("discos_lista"),
    })


@login_required
@permission_required("discosApp.view_disco", raise_exception=True)
def documento(request, disco_id):
    disco = get_object_or_404(Disco, pk=disco_id)
    if not disco.documento:
        raise Http404("El disco no tiene documento.")
    try:
        archivo = disco.documento.open("rb")
    except FileNotFoundError:
        raise Http404("El documento no está disponible.")
    return FileResponse(archivo, as_attachment=True, filename=Path(disco.documento.name).name, content_type="application/pdf")

