from django import forms

from artistasApp.models import Artista


class ArtistaForm(forms.ModelForm):
    class Meta:
        model = Artista
        fields = ["nombre", "genero", "pais", "anio_formacion", "integrantes", "bio", "imagen"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "genero": forms.TextInput(attrs={"class": "form-control"}),
            "pais": forms.TextInput(attrs={"class": "form-control"}),
            "anio_formacion": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "integrantes": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "bio": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "imagen": forms.ClearableFileInput(attrs={"class": "form-control", "accept": "image/jpeg,image/png,image/webp"}),
        }
