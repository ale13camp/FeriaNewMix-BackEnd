from django import forms


class CompraForm(forms.Form):
    cantidad = forms.IntegerField(
        label="Cantidad", min_value=1, max_value=2147483647,
        widget=forms.NumberInput(attrs={"class": "form-control", "min": 1, "step": 1}),
    )


class BusquedaComprasForm(forms.Form):
    q = forms.CharField(
        label="Buscar por título del disco", required=False, max_length=200,
        widget=forms.TextInput(attrs={"class": "form-control", "type": "search"}),
    )
    fecha_desde = forms.DateField(
        label="Fecha desde", required=False, input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"class": "form-control", "type": "date"}),
        error_messages={"invalid": "Ingresa una fecha válida (año-mes-día)."},
    )
    fecha_hasta = forms.DateField(
        label="Fecha hasta", required=False, input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"class": "form-control", "type": "date"}),
        error_messages={"invalid": "Ingresa una fecha válida (año-mes-día)."},
    )

    def clean(self):
        datos = super().clean()
        desde = datos.get("fecha_desde")
        hasta = datos.get("fecha_hasta")
        if desde and hasta and desde > hasta:
            raise forms.ValidationError("La fecha desde no puede ser posterior a la fecha hasta.")
        return datos
