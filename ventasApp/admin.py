from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.shortcuts import redirect
from .forms import ClienteForm, VentaForm
from .models import Cliente, Venta


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    form = ClienteForm
    list_display = ["nombre", "correo", "telefono"]
    search_fields = ["nombre", "correo", "telefono"]


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    form = VentaForm
    list_display = ["id", "fecha", "cliente", "disco", "cantidad", "precio_unitario", "total_clp"]
    list_filter = ["fecha", "disco__artista"]
    search_fields = ["cliente__nombre", "cliente__correo", "disco__titulo", "disco__artista__nombre"]
    list_select_related = ["cliente", "disco", "disco__artista"]
    # Borrar una instancia pasa por Venta.delete y devuelve el stock.
    actions = None

    @admin.display(description="Total (CLP)")
    def total_clp(self, obj):
        return obj.total

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        try:
            return super().changeform_view(request, object_id, form_url, extra_context)
        except ValidationError as error:
            # La transacción del Admin ya se revirtió. Otra venta pudo consumir stock.
            self.message_user(request, " ".join(error.messages), level=messages.ERROR)
            return redirect(request.path)
