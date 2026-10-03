import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from artistasApp.forms import ArtistaForm
from artistasApp.models import Artista
from discosApp.models import Disco


def home(request):
    artistas = Artista.objects.all()
    discos_destacados = []
    artistas_vistos = set()
    for disco in Disco.objects.select_related("artista").order_by("id"):
        if disco.artista_id not in artistas_vistos:
            discos_destacados.append(disco)
            artistas_vistos.add(disco.artista_id)
        if len(discos_destacados) == 8:
            break
    return render(request, "home.html", {
        "total_artistas": artistas.count(),
        "total_discos": Disco.objects.count(),
        "total_generos": artistas.values("genero").distinct().count(),
        "artistas_destacados": artistas[:3],
        "discos_destacados": discos_destacados,
    })


@login_required
@permission_required("artistasApp.view_artista", raise_exception=True)
def inicio(request):
    artistas = Artista.objects.order_by("id")
    total = artistas.count()
    artista_del_dia = artistas[datetime.date.today().toordinal() % total] if total else None
    return render(request, "artistas/inicio.html", {
        "total_artistas": total, "artista_del_dia": artista_del_dia,
    })


def filtrar_artistas(request):
    artistas = Artista.objects.all()
    q = request.GET.get("q", "").strip()
    genero = request.GET.get("genero", "")
    pais = request.GET.get("pais", "")
    if q:
        artistas = artistas.filter(Q(nombre__icontains=q) | Q(pais__icontains=q))
    if genero:
        artistas = artistas.filter(genero=genero)
    if pais:
        artistas = artistas.filter(pais=pais)
    return {
        "artistas": artistas,
        "generos": Artista.objects.order_by("genero").values_list("genero", flat=True).distinct(),
        "paises": Artista.objects.order_by("pais").values_list("pais", flat=True).distinct(),
        "q": q, "genero_filtro": genero, "pais_filtro": pais, "total": artistas.count(),
    }


@login_required
@permission_required("artistasApp.view_artista", raise_exception=True)
def catalogo(request):
    return render(request, "artistas/catalogo.html", filtrar_artistas(request))


@login_required
@permission_required("artistasApp.view_artista", raise_exception=True)
def detalle(request, artista_id):
    artista = get_object_or_404(Artista, pk=artista_id)
    return render(request, "artistas/detalle.html", {
        "artista": artista, "antiguedad": datetime.date.today().year - artista.anio_formacion,
    })


@login_required
@permission_required("artistasApp.view_artista", raise_exception=True)
def lista(request):
    return render(request, "artistas/lista.html", filtrar_artistas(request))


@login_required
@permission_required("artistasApp.add_artista", raise_exception=True)
def crear(request):
    form = ArtistaForm(request.POST if request.method == "POST" else None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Artista creado.")
        return redirect("artistas_lista")
    return render(request, "comunes/formulario.html", {
        "titulo": "Agregar artista", "form": form, "volver_url": reverse("artistas_lista"),
    })


@login_required
@permission_required("artistasApp.change_artista", raise_exception=True)
def editar(request, artista_id):
    artista = get_object_or_404(Artista, pk=artista_id)
    form = ArtistaForm(request.POST if request.method == "POST" else None, request.FILES or None, instance=artista)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Artista actualizado.")
        return redirect("artistas_lista")
    return render(request, "comunes/formulario.html", {
        "titulo": "Editar artista", "form": form, "volver_url": reverse("artistas_lista"),
    })


@login_required
@permission_required("artistasApp.delete_artista", raise_exception=True)
def eliminar(request, artista_id):
    artista = get_object_or_404(Artista, pk=artista_id)
    if request.method == "POST":
        try:
            artista.delete()
            messages.success(request, "Artista eliminado.")
        except ProtectedError:
            messages.error(request, "No se puede eliminar el artista porque tiene discos asociados.")
        return redirect("artistas_lista")
    return render(request, "comunes/eliminar.html", {
        "titulo": "Eliminar artista", "objeto": artista, "volver_url": reverse("artistas_lista"),
    })

