from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class RegistroClienteForm(UserCreationForm):
    nombre = forms.CharField(label="Nombre", max_length=150)
    correo = forms.EmailField(label="Correo electrónico", max_length=254)
    telefono = forms.CharField(label="Teléfono", max_length=30, required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ["username", "nombre", "correo", "telefono", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        autocompletar = {
            "username": "username", "nombre": "name", "correo": "email",
            "telefono": "tel", "password1": "new-password", "password2": "new-password",
        }
        for nombre, campo in self.fields.items():
            campo.widget.attrs.update({
                "class": "form-control", "autocomplete": autocompletar[nombre],
            })
        self.fields["telefono"].widget.attrs["type"] = "tel"

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.first_name = self.cleaned_data["nombre"]
        usuario.email = self.cleaned_data["correo"]
        if commit:
            usuario.save()
        return usuario
