import factory

from apps.farms.models import CropCategory, Farm, FarmFollow, FarmProduct, Invitation


class FarmFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Farm

    name = factory.Sequence(lambda n: f"Ferme {n}")
    description = ""
    address = ""
    phone = ""
    is_active = True


class CropCategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CropCategory

    name = factory.Sequence(lambda n: f"Catégorie {n}")
    description = ""
    icon = ""


class FarmProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FarmProduct

    farm = factory.SubFactory(FarmFactory)
    crop_category = factory.SubFactory(CropCategoryFactory)
    name = factory.Sequence(lambda n: f"Produit {n}")
    default_unit = FarmProduct.Unit.KG
    default_price = "2.50"
    is_active = True


class FarmFollowFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FarmFollow

    follower_farm = factory.SubFactory(FarmFactory)
    followed_farm = factory.SubFactory(FarmFactory)


class InvitationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Invitation

    email = factory.Sequence(lambda n: f"invite{n}@example.com")
    invited_by = None
