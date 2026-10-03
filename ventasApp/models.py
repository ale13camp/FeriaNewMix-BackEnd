from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone

from discosApp.models import Disco


class Cliente(models.Model):
    nombre = models.CharField(max_length=150)
    correo = models.EmailField()
    telefono = models.CharField("teléfono", max_length=30, blank=True)

    class Meta:
        ordering = ["nombre", "pk"]

    def __str__(self):
        return self.nombre


class Venta(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name="ventas")
    disco = models.ForeignKey("discosApp.Disco", on_delete=models.PROTECT, related_name="ventas")
    fecha = models.DateField(default=timezone.localdate)
    cantidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    precio_unitario = models.DecimalField("precio unitario (CLP)", max_digits=10, decimal_places=0,
                                         validators=[MinValueValidator(1)])

    class Meta:
        ordering = ["-fecha", "-pk"]
        constraints = [
            models.CheckConstraint(condition=models.Q(cantidad__gte=1), name="venta_cantidad_positiva"),
            models.CheckConstraint(condition=models.Q(precio_unitario__gte=1), name="venta_precio_positivo"),
        ]

    @property
    def total(self):
        return self.cantidad * self.precio_unitario

    def __str__(self):
        return f"Venta {self.pk or 'nueva'}: {self.cliente} — {self.disco}"

    def clean(self):
        # ModelForm usa esta comprobación para mostrar un error en cantidad.
        if not self.disco_id or not self.cantidad or self.cantidad < 1:
            return
        disco = Disco.objects.filter(pk=self.disco_id).first()
        anterior = Venta.objects.filter(pk=self.pk).first() if self.pk else None
        disponible = disco.stock if disco else 0
        if anterior and anterior.disco_id == self.disco_id:
            disponible += anterior.cantidad
        if disco and self.cantidad > disponible:
            raise ValidationError({"cantidad": f"Stock insuficiente. Hay {disponible} unidades disponibles."})

    def save(self, *args, **kwargs):
        # Un guardado completo mantiene juntos la venta y el movimiento de stock.
        if kwargs.get("update_fields") is not None:
            raise ValidationError("Guarda la venta completa para mantener su stock.")
        using = kwargs.get("using") or self._state.db or "default"
        with transaction.atomic(using=using):
            anterior = Venta.objects.using(using).select_for_update().filter(pk=self.pk).first() if self.pk else None
            if self.pk and not self._state.adding and anterior is None:
                raise ValidationError("Esta venta ya fue eliminada. Actualiza la lista.")
            self.full_clean()
            ids = {self.disco_id}
            if anterior:
                ids.add(anterior.disco_id)
            # Orden fijo si se cambia de disco, para evitar bloqueos cruzados.
            discos = {disco.pk: disco for disco in Disco.objects.using(using).select_for_update().filter(pk__in=ids).order_by("pk")}
            nuevos_stocks = {pk: disco.stock for pk, disco in discos.items()}
            if anterior:
                nuevos_stocks[anterior.disco_id] += anterior.cantidad
            disponible = nuevos_stocks[self.disco_id]
            if self.cantidad > disponible:
                raise ValidationError({"cantidad": f"Stock insuficiente. Hay {disponible} unidades disponibles."})
            nuevos_stocks[self.disco_id] -= self.cantidad
            super().save(*args, **kwargs)
            for pk, stock in nuevos_stocks.items():
                Disco.objects.using(using).filter(pk=pk).update(stock=stock)

    def delete(self, using=None, keep_parents=False):
        using = using or self._state.db or "default"
        with transaction.atomic(using=using):
            anterior = Venta.objects.using(using).select_for_update().filter(pk=self.pk).first()
            if anterior is None:
                return 0, {}
            disco = Disco.objects.using(using).select_for_update().get(pk=anterior.disco_id)
            resultado = super().delete(using=using, keep_parents=keep_parents)
            Disco.objects.using(using).filter(pk=disco.pk).update(stock=disco.stock + anterior.cantidad)
            return resultado
