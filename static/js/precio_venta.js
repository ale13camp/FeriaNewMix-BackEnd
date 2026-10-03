function prepararPrecioVenta() {
    const disco = document.getElementById("id_disco");
    const precio = document.getElementById("id_precio_unitario");
    if (!disco || !precio) return;
    let consultaActual = 0;

    async function actualizarPrecio() {
        const consulta = ++consultaActual;
        const discoId = disco.value;
        const opcion = disco.options[disco.selectedIndex];
        // Al editar el mismo disco se conserva el precio histórico de la venta.
        if (discoId && discoId === precio.dataset.discoOriginal) {
            precio.value = precio.dataset.precioOriginal;
            return;
        }
        precio.value = opcion?.dataset.precio || "";
        if (!discoId) return;

        // También obtiene el precio de discos creados o editados desde el Admin.
        try {
            const url = disco.dataset.precioUrl.replace("/0/", `/${encodeURIComponent(discoId)}/`);
            const respuesta = await fetch(url, {cache: "no-store"});
            if (!respuesta.ok) return;
            const datos = await respuesta.json();
            if (consulta === consultaActual && disco.value === discoId) {
                precio.value = datos.precio;
                opcion.dataset.precio = datos.precio;
            }
        } catch {
            // Si falla la consulta, se mantiene el precio cargado en la opción.
        }
    }

    if (window.django?.jQuery) {
        window.django.jQuery(disco).on("change", actualizarPrecio);
    } else {
        disco.addEventListener("change", actualizarPrecio);
    }
    actualizarPrecio();
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", prepararPrecioVenta);
} else {
    prepararPrecioVenta();
}
