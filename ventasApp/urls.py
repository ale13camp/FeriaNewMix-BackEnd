from django.urls import path
from . import views, views_compra


urlpatterns = [
    path("mis-compras/", views_compra.compras_lista, name="compras_lista"),
    path("comprar/<int:disco_id>/", views_compra.compra_crear, name="compra_crear"),
    path("", views.ventas_lista, name="ventas_lista"),
    path("nueva/", views.ventas_crear, name="ventas_crear"),
    path("<int:pk>/editar/", views.ventas_editar, name="ventas_editar"),
    path("<int:pk>/eliminar/", views.ventas_eliminar, name="ventas_eliminar"),
    path("clientes/", views.clientes_lista, name="clientes_lista"),
    path("clientes/nuevo/", views.clientes_crear, name="clientes_crear"),
    path("clientes/<int:pk>/editar/", views.clientes_editar, name="clientes_editar"),
    path("clientes/<int:pk>/eliminar/", views.clientes_eliminar, name="clientes_eliminar"),
]
