from django import forms

from discosApp.models import Disco


class DiscoForm(forms.ModelForm):
    class Meta:
        model = Disco
        fields = ["titulo", "artista", "genero", "anio", "formato", "precio", "stock", "descripcion", "imagen", "documento"]
        widgets = {
            "titulo": forms.TextInput(attrs={"class": "form-control"}),
            "artista": forms.Select(attrs={"class": "form-select"}),
            "genero": forms.TextInput(attrs={"class": "form-control"}),
            "anio": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "formato": forms.Select(attrs={"class": "form-select"}),
            "precio": forms.NumberInput(attrs={"class": "form-control", "min": 1, "step": 1}),
            "stock": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "descripcion": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "imagen": forms.ClearableFileInput(attrs={"class": "form-control", "accept": "image/jpeg,image/png,image/webp"}),
            "documento": forms.FileInput(attrs={"class": "form-control", "accept": ".pdf"}),
        }
        help_texts = {"imagen": "JPG, PNG o WebP; máximo 5 MB.", "documento": "PDF opcional; máximo 10 MB. Al editar, deje vacío para conservarlo."}
