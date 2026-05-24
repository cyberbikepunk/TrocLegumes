"""
Seed the database with dev data: categories, farms, farm products, and the current week.

Usage:
    docker compose exec web python manage.py seed_dev
    docker compose exec web python manage.py seed_dev --clear   # wipe first
"""

import logging
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.farms.models import CropCategory, Farm, FarmFollow, FarmProduct
from apps.market.models import Listing, Week

logger = logging.getLogger(__name__)

User = get_user_model()

CATEGORIES = [
    ("Légumes", "bi-flower1"),
    ("Fruits", "bi-apple"),
    ("Herbes aromatiques", "bi-tree"),
    ("Céréales", "bi-sun"),
    ("Légumineuses", "bi-dot"),
    ("Œufs & Laitiers", "bi-egg"),
    ("Produits transformés", "bi-jar"),
]

FARMS = [
    {
        "name": "La Ferme des Collines",
        "description": "Maraîchage bio en permaculture, vallée de l'Huveaune.",
        "address": "1 chemin des Collines, 13400 Aubagne",
        "phone": "06 11 22 33 44",
        "latitude": 43.29,
        "longitude": 5.57,
        "user_email": "collines@example.com",
        "user_first": "Adèle",
        "user_last": "Martin",
    },
    {
        "name": "Le Potager du Soleil",
        "description": "Légumes et petits fruits, culture raisonnée.",
        "address": "12 route du Moulin, 13300 Salon-de-Provence",
        "phone": "06 55 66 77 88",
        "latitude": 43.64,
        "longitude": 5.10,
        "user_email": "soleil@example.com",
        "user_first": "Baptiste",
        "user_last": "Dupont",
    },
    {
        "name": "Mas Sauvage",
        "description": "Céréales et légumineuses bio, plaine de la Crau.",
        "address": "Mas Sauvage, 13310 Saint-Martin-de-Crau",
        "phone": "06 99 00 11 22",
        "latitude": 43.64,
        "longitude": 4.82,
        "user_email": "massauvage@example.com",
        "user_first": "Camille",
        "user_last": "Roux",
    },
]

PRODUCTS = [
    # (farm_index, category_name, name, unit, price)
    (0, "Légumes", "Tomates cerises cœur de bœuf", "kg", "4.50"),
    (0, "Légumes", "Courgettes rondes", "kg", "2.00"),
    (0, "Herbes aromatiques", "Basilic grand vert", "bouquet", "1.50"),
    (1, "Légumes", "Carottes des sables", "botte", "2.50"),
    (1, "Fruits", "Melons charentais", "pièce", "3.00"),
    (1, "Légumes", "Pommes de terre Charlotte", "kg", "1.80"),
    (2, "Céréales", "Farine de blé T65", "kg", "2.20"),
    (2, "Légumineuses", "Lentilles vertes du Puy", "kg", "3.50"),
]


def _current_week_bounds():
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday


class Command(BaseCommand):
    help = "Seed the database with dev data (farms, categories, products, current week)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all seed data before re-creating it.",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self._clear()

        categories = self._seed_categories()
        farms = self._seed_farms()
        self._seed_products(farms, categories)
        self._seed_week(farms, categories)
        self._seed_follows(farms)

        self.stdout.write(self.style.SUCCESS("Dev seed complete."))
        logger.info("Dev seed completed successfully.")

    def _clear(self):
        self.stdout.write("Clearing existing seed data...")
        Listing.objects.all().delete()
        Week.objects.all().delete()
        FarmProduct.objects.all().delete()
        FarmFollow.objects.all().delete()
        Farm.objects.all().delete()
        CropCategory.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        self.stdout.write(self.style.WARNING("Cleared."))

    def _seed_categories(self):
        categories = {}
        for name, icon in CATEGORIES:
            cat, created = CropCategory.objects.get_or_create(name=name, defaults={"icon": icon})
            categories[name] = cat
            if created:
                self.stdout.write(f"  + Catégorie : {name}")
        return categories

    def _seed_farms(self):
        farms = []
        for data in FARMS:
            user, _ = User.objects.get_or_create(
                email=data["user_email"],
                defaults={
                    "first_name": data["user_first"],
                    "last_name": data["user_last"],
                    "phone": data["phone"],
                },
            )
            if not user.has_usable_password():
                user.set_password("troclegumes")
                user.save()

            farm, created = Farm.objects.get_or_create(
                name=data["name"],
                defaults={
                    "description": data["description"],
                    "address": data["address"],
                    "phone": data["phone"],
                    "latitude": data["latitude"],
                    "longitude": data["longitude"],
                },
            )
            if created:
                self.stdout.write(f"  + Ferme : {farm.name}")

            if user.farm_id != farm.pk:
                user.farm = farm
                user.save(update_fields=["farm"])

            farms.append(farm)
        return farms

    def _seed_products(self, farms, categories):
        for farm_idx, cat_name, name, unit, price in PRODUCTS:
            farm = farms[farm_idx]
            category = categories[cat_name]
            product, created = FarmProduct.objects.get_or_create(
                farm=farm,
                name=name,
                defaults={
                    "crop_category": category,
                    "default_unit": unit,
                    "default_price": price,
                },
            )
            if created:
                self.stdout.write(f"  + Produit : {name} ({farm.name})")

    def _seed_week(self, farms, categories):
        monday, sunday = _current_week_bounds()
        week, created = Week.objects.get_or_create(
            start_date=monday,
            defaults={"end_date": sunday, "is_active": True},
        )
        if created:
            self.stdout.write(f"  + Semaine : {monday} → {sunday}")

        # Activate only this week
        Week.objects.exclude(pk=week.pk).update(is_active=False)
        if not week.is_active:
            week.is_active = True
            week.save(update_fields=["is_active"])

        # Create a listing for each seeded product
        for product in FarmProduct.objects.select_related("farm").all():
            listing, created = Listing.objects.get_or_create(
                farm_product=product,
                farm=product.farm,
                week=week,
                defaults={
                    "quantity_available": 20,
                    "unit": product.default_unit,
                    "price_per_unit": product.default_price,
                },
            )
            if created:
                self.stdout.write(f"  + Annonce : {product.name} — {product.farm.name}")

    def _seed_follows(self, farms):
        # Each farm follows the other two
        pairs = [(farms[0], farms[1]), (farms[0], farms[2]), (farms[1], farms[2]), (farms[1], farms[0]), (farms[2], farms[0]), (farms[2], farms[1])]
        for follower, followed in pairs:
            _, created = FarmFollow.objects.get_or_create(follower_farm=follower, followed_farm=followed)
            if created:
                self.stdout.write(f"  + Follow : {follower} → {followed}")
