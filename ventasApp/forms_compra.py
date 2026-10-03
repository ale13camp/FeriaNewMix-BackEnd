from django import forms


class CompraForm(forms.Form):
    cantidad = forms.IntegerField(
        label="Cantidad", min_value=1, max_value=2147483647,
        widget=forms.NumberInput(attrs={"class": "form-control", "min": 1, "step": 1}),
    )
