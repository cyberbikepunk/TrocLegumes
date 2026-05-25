import logging

from django.db import models

from apps.farms.models import CropCategory, Farm, FarmProduct

logger = logging.getLogger(__name__)


class Week(models.Model):
    start_date = models.DateField(verbose_name="Début (lundi)")
    end_date = models.DateField(verbose_name="Fin (dimanche)")
    is_active = models.BooleanField(default=False, verbose_name="Semaine active")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Semaine"
        verbose_name_plural = "Semaines"
        ordering = ["-start_date"]

    def __str__(self):
        return f"Semaine du {self.start_date} au {self.end_date}"

    def save(self, *args, **kwargs):
        if self.is_active:
            Week.objects.exclude(pk=self.pk).filter(is_active=True).update(is_active=False)
        super().save(*args, **kwargs)


class Listing(models.Model):
    farm_product = models.ForeignKey(
        FarmProduct,
        on_delete=models.PROTECT,
        related_name="listings",
        verbose_name="Produit",
    )
    farm = models.ForeignKey(
        Farm,
        on_delete=models.CASCADE,
        related_name="listings",
        verbose_name="Ferme",
    )
    week = models.ForeignKey(
        Week,
        on_delete=models.PROTECT,
        related_name="listings",
        verbose_name="Semaine",
    )
    quantity_available = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Quantité disponible",
    )
    unit = models.CharField(
        max_length=20,
        choices=FarmProduct.Unit.choices,
        verbose_name="Unité",
    )
    price_per_unit = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name="Prix à l'unité (€)",
    )
    notes = models.TextField(blank=True, verbose_name="Notes")
    is_active = models.BooleanField(default=True, verbose_name="Active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Annonce"
        verbose_name_plural = "Annonces"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.farm_product.name} — {self.farm} ({self.week})"


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "En attente"
        ACCEPTED = "accepted", "Acceptée"
        CONFIRMED = "confirmed", "Confirmée"
        DECLINED = "declined", "Refusée"
        CANCELLED = "cancelled", "Annulée"

    buyer_farm = models.ForeignKey(
        Farm,
        on_delete=models.PROTECT,
        related_name="orders_as_buyer",
        verbose_name="Ferme acheteuse",
    )
    seller_farm = models.ForeignKey(
        Farm,
        on_delete=models.PROTECT,
        related_name="orders_as_seller",
        verbose_name="Ferme vendeuse",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="Statut",
    )
    buyer_notes = models.TextField(blank=True, verbose_name="Notes de l'acheteur")
    seller_notes = models.TextField(blank=True, verbose_name="Notes du vendeur")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Commande"
        verbose_name_plural = "Commandes"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Commande #{self.pk} — {self.buyer_farm} → {self.seller_farm} ({self.get_status_display()})"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Commande",
    )
    listing = models.ForeignKey(
        Listing,
        on_delete=models.PROTECT,
        related_name="order_items",
        verbose_name="Annonce",
    )
    quantity = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Quantité")
    unit_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name="Prix unitaire (€)",
    )
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Prix total (€)",
    )
    notes = models.TextField(blank=True, verbose_name="Notes")

    class Meta:
        verbose_name = "Ligne de commande"
        verbose_name_plural = "Lignes de commande"

    def __str__(self):
        return f"{self.listing.farm_product.name} × {self.quantity}"


class WantedListing(models.Model):
    farm = models.ForeignKey(
        Farm,
        on_delete=models.CASCADE,
        related_name="wanted_listings",
        verbose_name="Ferme",
    )
    crop_category = models.ForeignKey(
        CropCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="wanted_listings",
        verbose_name="Catégorie",
    )
    description = models.TextField(verbose_name="Description")
    quantity_wanted = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Quantité souhaitée",
    )
    unit = models.CharField(
        max_length=20,
        choices=FarmProduct.Unit.choices,
        blank=True,
        verbose_name="Unité",
    )
    week = models.ForeignKey(
        Week,
        on_delete=models.PROTECT,
        related_name="wanted_listings",
        verbose_name="Semaine",
    )
    is_fulfilled = models.BooleanField(default=False, verbose_name="Satisfaite")
    is_active = models.BooleanField(default=True, verbose_name="Active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Demande"
        verbose_name_plural = "Demandes"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Demande : {self.description[:50]} — {self.farm}"


class WantedResponse(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "En attente"
        ACCEPTED = "accepted", "Acceptée"
        DECLINED = "declined", "Refusée"

    wanted_listing = models.ForeignKey(
        WantedListing,
        on_delete=models.CASCADE,
        related_name="responses",
        verbose_name="Demande",
    )
    responding_farm = models.ForeignKey(
        Farm,
        on_delete=models.CASCADE,
        related_name="wanted_responses",
        verbose_name="Ferme répondante",
    )
    quantity_offered = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Quantité proposée",
    )
    notes = models.TextField(blank=True, verbose_name="Notes")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="Statut",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Réponse à une demande"
        verbose_name_plural = "Réponses aux demandes"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Réponse de {self.responding_farm} à {self.wanted_listing}"
