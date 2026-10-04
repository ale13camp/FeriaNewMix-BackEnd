from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views

app_name = "discosApi"

urlpatterns = [
    path("clientes/", views.clientes_lista, name="clientes_lista"),
    path("clientes/<int:pk>/", views.clientes_detalle, name="clientes_detalle"),
    path("discos/", views.discos_lista, name="discos_lista"),
    path("discos/<int:pk>/", views.discos_detalle, name="discos_detalle"),
    path("ventas/", views.ventas_lista, name="ventas_lista"),
    path("ventas/<int:pk>/", views.ventas_detalle, name="ventas_detalle"),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("schema/", SpectacularAPIView.as_view(permission_classes=[AllowAny], authentication_classes=[]), name="schema"),
    path("swagger/", SpectacularSwaggerView.as_view(url_name="discosApi:schema", permission_classes=[AllowAny], authentication_classes=[]), name="swagger"),
    path("redoc/", SpectacularRedocView.as_view(url_name="discosApi:schema", permission_classes=[AllowAny], authentication_classes=[]), name="redoc"),
]
