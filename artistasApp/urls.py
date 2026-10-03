from django.urls import path

from artistasApp import views

urlpatterns = [
    path("", views.inicio, name="artistas_inicio"),
    path("catalogo/", views.catalogo, name="artistas_catalogo"),
    path("detalle/<int:artista_id>/", views.detalle, name="artistas_detalle"),
    path("lista/", views.lista, name="artistas_lista"),
    path("crear/", views.crear, name="artistas_crear"),
    path("editar/<int:artista_id>/", views.editar, name="artistas_editar"),
    path("eliminar/<int:artista_id>/", views.eliminar, name="artistas_eliminar"),
]
