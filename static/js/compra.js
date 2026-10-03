document.addEventListener("DOMContentLoaded", function () {
    const cantidad = document.getElementById("id_cantidad");
    const total = document.getElementById("total-compra");
    if (!cantidad || !total) return;
    const precio = Number(total.dataset.precio);
    const formato = new Intl.NumberFormat("es-CL");

    function actualizarTotal() {
        const unidades = cantidad.valueAsNumber;
        total.textContent = Number.isInteger(unidades) && unidades > 0 && cantidad.validity.valid
            ? "$" + formato.format(precio * unidades) + " CLP"
            : "—";
    }
    cantidad.addEventListener("input", actualizarTotal);
    actualizarTotal();
});
