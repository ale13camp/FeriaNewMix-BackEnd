function prepararPrecioVenta() {
    const disco = document.getElementById("id_disco");
    const precio = document.getElementById("id_precio_unitario");
    if (!disco || !precio) return;

    function actualizarPrecio() {
        const opcion = disco.options[disco.selectedIndex];
        // Al editar el mismo disco se conserva el precio histórico de la venta.
        precio.value = disco.value && disco.value === precio.dataset.discoOriginal
            ? precio.dataset.precioOriginal
            : opcion?.dataset.precio || "";
    }

    disco.addEventListener("change", actualizarPrecio);
    actualizarPrecio();
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", prepararPrecioVenta);
} else {
    prepararPrecioVenta();
}
