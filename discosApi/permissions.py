from rest_framework.permissions import BasePermission


def rol_usuario(usuario):
    """El primer grupo válido determina el rol; se consulta en cada petición."""
    if not usuario.is_authenticated:
        return None
    if usuario.is_superuser:
        return "Administrador"
    grupos = set(usuario.groups.values_list("name", flat=True))
    for rol in ("Administrador", "Operador", "Consulta", "Cliente"):
        if rol in grupos:
            return rol
    return None


class PermisoGrupoApi(BasePermission):
    message = "Tu perfil no permite esta operación."

    def has_permission(self, request, view):
        request.rol_api = rol_usuario(request.user)
        if request.rol_api == "Administrador":
            return True
        if request.rol_api == "Operador":
            return request.method in ("GET", "POST", "PUT", "HEAD", "OPTIONS")
        if request.rol_api == "Consulta":
            return request.method in ("GET", "HEAD", "OPTIONS")
        if request.rol_api == "Cliente":
            return request.method in ("GET", "HEAD", "OPTIONS") or (
                request.method == "POST" and view.__class__.__name__ == "ventas_lista"
            )
        return False
