from django.urls import path

from discosApp import views

urlpatterns = [
    path("", views.inicio, name="discos_inicio"),
    path("catalogo/", views.catalogo, name="discos_catalogo"),
    path("detalle/<int:disco_id>/", views.detalle, name="discos_detalle"),
    path("lista/", views.lista, name="discos_lista"),
    path("crear/", views.crear, name="discos_crear"),
    path("editar/<int:disco_id>/", views.editar, name="discos_editar"),
    path("eliminar/<int:disco_id>/", views.eliminar, name="discos_eliminar"),
    path("documento/<int:disco_id>/", views.documento, name="discos_documento"),
]
