import logging
from decimal import Decimal

from django.conf import settings
from django.db import models

from apps.farms.models import Farm

logger = logging.getLogger(__name__)


class Settlement(models.Model):
    class Type(models.TextChoices):
        MONETARY = "monetary", "Monétaire"
        LABOR = "labor", "Échange de travail"
        MUTUAL_WRITEOFF = "mutual_writeoff", "Annulation mutuelle"

    class Method(models.TextChoices):
        CASH = "cash", "Espèces"
        VIREMENT = "virement", "Virement"

    class Status(models.TextChoices):
        PENDING = "pending", "En attente"
        CONFIRMED = "confirmed", "Confirmé"
        DISPUTED = "disputed", "Contesté"

    farm_a = models.ForeignKey(
        Farm,
        on_delete=models.PROTECT,
        related_name="settlements_as_a",
        verbose_name="Ferme A (proposante)",
    )
    farm_b = models.ForeignKey(
        Farm,
        on_delete=models.PROTECT,
        related_name="settlements_as_b",
        verbose_name="Ferme B (contrepartie)",
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant (€)")
    type = models.CharField(max_length=20, choices=Type.choices, verbose_name="Type")
    method = models.CharField(
        max_length=20,
        choices=Method.choices,
        blank=True,
        verbose_name="Méthode (si monétaire)",
    )
    description = models.TextField(verbose_name="Description")
    proposed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="settlements_proposed",
        verbose_name="Proposé par",
    )
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="settlements_confirmed",
        verbose_name="Confirmé par",
    )
    confirmed_at = models.DateTimeField(null=True, blank=True, verbose_name="Confirmé le")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="Statut",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Règlement"
        verbose_name_plural = "Règlements"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Règlement {self.farm_a} ↔ {self.farm_b} ({self.amount} €)"


class TabEntry(models.Model):
    class EntryType(models.TextChoices):
        ORDER = "order", "Commande"
        SETTLEMENT = "settlement", "Règlement"
        ADJUSTMENT = "adjustment", "Ajustement"

    farm = models.ForeignKey(
        Farm,
        on_delete=models.PROTECT,
        related_name="tab_entries",
        verbose_name="Ferme",
    )
    order = models.ForeignKey(
        "market.Order",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="tab_entries",
        verbose_name="Commande",
    )
    settlement = models.ForeignKey(
        Settlement,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="tab_entries",
        verbose_name="Règlement",
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Montant (positif = crédit, négatif = débit)",
    )
    balance_after = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Solde global après",
    )
    entry_type = models.CharField(
        max_length=20,
        choices=EntryType.choices,
        verbose_name="Type d'entrée",
    )
    description = models.TextField(verbose_name="Description")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Entrée de compte"
        verbose_name_plural = "Entrées de compte"
        ordering = ["-created_at"]

    def __str__(self):
        amount = Decimal(str(self.amount))
        sign = "+" if amount >= 0 else ""
        return f"TabEntry {self.farm} {sign}{amount} € ({self.get_entry_type_display()})"
