import logging
import secrets

from django.conf import settings
from django.db import models

logger = logging.getLogger(__name__)


class Farm(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nom de la ferme")
    description = models.TextField(blank=True, verbose_name="Description")
    address = models.CharField(max_length=500, blank=True, verbose_name="Adresse")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone")
    logo = models.ImageField(upload_to="farms/logos/", blank=True, null=True, verbose_name="Logo")
    latitude = models.FloatField(null=True, blank=True, verbose_name="Latitude")
    longitude = models.FloatField(null=True, blank=True, verbose_name="Longitude")
    is_active = models.BooleanField(default=True, verbose_name="Active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Ferme"
        verbose_name_plural = "Fermes"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Clear stale coordinates when the address changes on an existing farm
        if self.pk and self.address:
            try:
                old = Farm.objects.get(pk=self.pk)
                if old.address != self.address:
                    self.latitude = None
                    self.longitude = None
            except Farm.DoesNotExist:
                pass
        super().save(*args, **kwargs)
        if self.address and not (self.latitude and self.longitude):
            self._geocode_address()

    def _geocode_address(self):
        from django.conf import settings
        from geopy.exc import GeocoderServiceError, GeocoderTimedOut
        from geopy.geocoders import Nominatim

        try:
            geolocator = Nominatim(user_agent=settings.GEOCODING_USER_AGENT)
            location = geolocator.geocode(self.address, timeout=10)
            if location:
                Farm.objects.filter(pk=self.pk).update(
                    latitude=location.latitude,
                    longitude=location.longitude,
                )
                self.latitude = location.latitude
                self.longitude = location.longitude
                logger.info(
                    "Geocoded farm %d '%s': (%.4f, %.4f)",
                    self.pk, self.name, self.latitude, self.longitude,
                )
            else:
                logger.warning(
                    "No geocoding result for farm %d address: %s", self.pk, self.address
                )
        except (GeocoderTimedOut, GeocoderServiceError) as exc:
            logger.error("Geocoding error for farm %d: %s", self.pk, exc)


class CropCategory(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nom")
    description = models.TextField(blank=True, verbose_name="Description")
    icon = models.CharField(max_length=50, blank=True, verbose_name="Icône (Bootstrap Icons)")

    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class FarmProduct(models.Model):
    class Unit(models.TextChoices):
        KG = "kg", "kg"
        G = "g", "g"
        LITRE = "litre", "litre"
        BOUQUET = "bouquet", "bouquet"
        BOTTE = "botte", "botte"
        PIECE = "pièce", "pièce"

    farm = models.ForeignKey(
        Farm,
        on_delete=models.CASCADE,
        related_name="products",
        verbose_name="Ferme",
    )
    crop_category = models.ForeignKey(
        CropCategory,
        on_delete=models.PROTECT,
        related_name="products",
        verbose_name="Catégorie",
    )
    name = models.CharField(max_length=200, verbose_name="Nom")
    description = models.TextField(blank=True, verbose_name="Description")
    default_unit = models.CharField(
        max_length=20,
        choices=Unit.choices,
        default=Unit.KG,
        verbose_name="Unité par défaut",
    )
    default_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name="Prix par défaut (€)",
    )
    photo = models.ImageField(
        upload_to="farms/products/",
        blank=True,
        null=True,
        verbose_name="Photo",
    )
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Produit"
        verbose_name_plural = "Produits"
        ordering = ["farm", "name"]

    def __str__(self):
        return f"{self.name} ({self.farm})"


class FarmFollow(models.Model):
    follower_farm = models.ForeignKey(
        Farm,
        on_delete=models.CASCADE,
        related_name="following",
        verbose_name="Ferme qui suit",
    )
    followed_farm = models.ForeignKey(
        Farm,
        on_delete=models.CASCADE,
        related_name="followers",
        verbose_name="Ferme suivie",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Abonnement"
        verbose_name_plural = "Abonnements"
        unique_together = [("follower_farm", "followed_farm")]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.follower_farm} → {self.followed_farm}"


class Invitation(models.Model):
    email = models.EmailField(verbose_name="Email")
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="invitations_sent",
        verbose_name="Invité par",
    )
    token = models.CharField(max_length=64, unique=True, default=secrets.token_urlsafe)
    used_at = models.DateTimeField(null=True, blank=True, verbose_name="Utilisée le")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Invitation"
        verbose_name_plural = "Invitations"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Invitation → {self.email}"
