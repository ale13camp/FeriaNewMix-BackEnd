from django import forms
from django.urls import reverse
from .models import Cliente, Venta


class DiscoConPrecioSelect(forms.Select):
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        opcion = super().create_option(name, value, label, selected, index, subindex, attrs)
        if value:
            opcion["attrs"]["data-precio"] = format(value.instance.precio, "f")
        return opcion


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ["nombre", "correo", "telefono"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "correo": forms.EmailInput(attrs={"class": "form-control"}),
            "telefono": forms.TextInput(attrs={"class": "form-control", "type": "tel"}),
        }


class VentaForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        disco_original = self.instance.disco_id if self.instance.pk else None
        precio_original = self.instance.precio_unitario
        self.fields["disco"].queryset = self.fields["disco"].queryset.select_related("artista")
        self.fields["disco"].widget.attrs["data-precio-url"] = reverse("discos_precio", args=[0])
        precio = self.fields["precio_unitario"]
        # Django ignora el precio enviado y utiliza el calculado aquí.
        precio.disabled = True
        precio.widget.attrs["data-disco-original"] = disco_original or ""
        precio.widget.attrs["data-precio-original"] = format(precio_original, "f") if disco_original else ""
        seleccionado = self.data.get(self.add_prefix("disco")) if self.is_bound else self.initial.get("disco")
        try:
            disco = self.fields["disco"].to_python(seleccionado)
        except forms.ValidationError:
            disco = None
        self.initial["precio_unitario"] = (
            precio_original if disco and disco.pk == disco_original else disco.precio if disco else None
        )

    class Media:
        js = ["js/precio_venta.js"]

    class Meta:
        model = Venta
        fields = ["cliente", "disco", "fecha", "cantidad", "precio_unitario"]
        widgets = {
            "cliente": forms.Select(attrs={"class": "form-select"}),
            "disco": DiscoConPrecioSelect(attrs={"class": "form-select"}),
            "fecha": forms.DateInput(format="%Y-%m-%d", attrs={"class": "form-control", "type": "date"}),
            "cantidad": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "precio_unitario": forms.NumberInput(attrs={"class": "form-control", "min": 1, "step": 1}),
        }
        help_texts = {"precio_unitario": "Se completa con el precio del disco seleccionado y se guarda en la venta."}
