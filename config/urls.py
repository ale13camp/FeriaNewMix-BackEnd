from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from artistasApp.views import home

urlpatterns = [
    path("admin/", admin.site.urls),
    #   path('lo_que_escribe_el_usuario_en_la_url',función_dentro_vista)
    path("artistas/", include("artistasApp.urls")),
    path("discos/", include("discosApp.urls")),
    path("ventas/", include("ventasApp.urls")),
    path("cuentas/", include("usuariosApp.urls")),
    path("cuentas/", include("django.contrib.auth.urls")),
    path("", home, name="home"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
