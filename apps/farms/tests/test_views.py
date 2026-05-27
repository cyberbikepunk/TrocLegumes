import pytest
from django.urls import reverse

from apps.accounts.tests.factories import UserFactory
from apps.farms.models import FarmFollow
from apps.farms.tests.factories import FarmFactory, FarmFollowFactory, FarmProductFactory


@pytest.fixture
def farm(db):
    return FarmFactory()


@pytest.fixture
def other_farm(db):
    return FarmFactory()


@pytest.fixture
def user_no_farm(db):
    user = UserFactory(farm=None)
    user.save()  # persist hashed password so force_login session hash matches
    return user


@pytest.fixture
def user_with_farm(db):
    f = FarmFactory()
    user = UserFactory(farm=f)
    user.save()  # persist hashed password so force_login session hash matches
    return user


class TestFarmListView:
    def test_get_returns_200(self, client, farm):
        response = client.get(reverse("farms:list"))
        assert response.status_code == 200

    def test_lists_only_active_farms(self, client, db):
        active = FarmFactory(is_active=True)
        inactive = FarmFactory(is_active=False)
        response = client.get(reverse("farms:list"))
        assert active in response.context["farms"]
        assert inactive not in response.context["farms"]

    def test_context_has_map_data(self, client, user_with_farm, other_farm):
        client.force_login(user_with_farm)
        response = client.get(reverse("farms:list"))
        assert "map_farms" in response.context
        assert "map_farms_json" in response.context
        assert "map_center_json" in response.context


class TestFarmDetailView:
    def test_get_returns_200(self, client, farm):
        response = client.get(reverse("farms:detail", kwargs={"pk": farm.pk}))
        assert response.status_code == 200

    def test_get_returns_404_for_unknown_farm(self, client, db):
        response = client.get(reverse("farms:detail", kwargs={"pk": 99999}))
        assert response.status_code == 404

    def test_is_own_farm_true_for_member(self, client, user_with_farm):
        client.force_login(user_with_farm)
        response = client.get(reverse("farms:detail", kwargs={"pk": user_with_farm.farm.pk}))
        assert response.context["is_own_farm"] is True

    def test_is_own_farm_false_for_other_farm(self, client, user_with_farm, other_farm):
        client.force_login(user_with_farm)
        response = client.get(reverse("farms:detail", kwargs={"pk": other_farm.pk}))
        assert response.context["is_own_farm"] is False


class TestFarmCreateView:
    def test_get_redirects_if_not_logged_in(self, client):
        response = client.get(reverse("farms:create"))
        assert response.status_code == 302

    def test_get_returns_200_for_user_without_farm(self, client, user_no_farm):
        client.force_login(user_no_farm)
        response = client.get(reverse("farms:create"))
        assert response.status_code == 200

    def test_get_redirects_if_user_already_has_farm(self, client, user_with_farm):
        client.force_login(user_with_farm)
        response = client.get(reverse("farms:create"))
        assert response.status_code == 302
        assert response["Location"] == reverse("farms:detail", kwargs={"pk": user_with_farm.farm.pk})

    def test_post_creates_farm_and_links_user(self, client, user_no_farm):
        client.force_login(user_no_farm)
        response = client.post(
            reverse("farms:create"),
            {"name": "Ma Nouvelle Ferme", "description": "", "address": "", "phone": ""},
        )
        assert response.status_code == 302
        user_no_farm.refresh_from_db()
        assert user_no_farm.farm is not None
        assert user_no_farm.farm.name == "Ma Nouvelle Ferme"


class TestFarmUpdateView:
    def test_get_redirects_if_not_logged_in(self, client, farm):
        response = client.get(reverse("farms:update", kwargs={"pk": farm.pk}))
        assert response.status_code == 302

    def test_get_returns_200_for_member(self, client, user_with_farm):
        client.force_login(user_with_farm)
        response = client.get(reverse("farms:update", kwargs={"pk": user_with_farm.farm.pk}))
        assert response.status_code == 200

    def test_get_returns_403_for_non_member(self, client, user_with_farm, other_farm):
        client.force_login(user_with_farm)
        response = client.get(reverse("farms:update", kwargs={"pk": other_farm.pk}))
        assert response.status_code == 403

    def test_post_updates_farm(self, client, user_with_farm):
        client.force_login(user_with_farm)
        response = client.post(
            reverse("farms:update", kwargs={"pk": user_with_farm.farm.pk}),
            {"name": "Ferme Modifiée", "description": "", "address": "", "phone": ""},
        )
        assert response.status_code == 302
        user_with_farm.farm.refresh_from_db()
        assert user_with_farm.farm.name == "Ferme Modifiée"


class TestFollowToggleView:
    def test_post_redirects_if_not_logged_in(self, client, farm):
        response = client.post(reverse("farms:follow_toggle", kwargs={"pk": farm.pk}))
        assert response.status_code == 302

    def test_post_creates_follow(self, client, user_with_farm, other_farm):
        client.force_login(user_with_farm)
        response = client.post(reverse("farms:follow_toggle", kwargs={"pk": other_farm.pk}))
        assert response.status_code == 200
        assert FarmFollow.objects.filter(
            follower_farm=user_with_farm.farm, followed_farm=other_farm
        ).exists()

    def test_post_deletes_existing_follow(self, client, user_with_farm, other_farm):
        FarmFollowFactory(follower_farm=user_with_farm.farm, followed_farm=other_farm)
        client.force_login(user_with_farm)
        response = client.post(reverse("farms:follow_toggle", kwargs={"pk": other_farm.pk}))
        assert response.status_code == 200
        assert not FarmFollow.objects.filter(
            follower_farm=user_with_farm.farm, followed_farm=other_farm
        ).exists()

    def test_post_own_farm_returns_200_without_follow(self, client, user_with_farm):
        client.force_login(user_with_farm)
        response = client.post(
            reverse("farms:follow_toggle", kwargs={"pk": user_with_farm.farm.pk})
        )
        assert response.status_code == 200
        assert not FarmFollow.objects.filter(
            follower_farm=user_with_farm.farm, followed_farm=user_with_farm.farm
        ).exists()


class TestFarmListFollowContext:
    def test_can_follow_false_for_unauthenticated(self, client, farm):
        response = client.get(reverse("farms:list"))
        assert response.context["can_follow"] is False

    def test_can_follow_true_for_user_with_farm(self, client, user_with_farm, other_farm):
        client.force_login(user_with_farm)
        response = client.get(reverse("farms:list"))
        assert response.context["can_follow"] is True

    def test_is_following_annotated_on_farms(self, client, user_with_farm, other_farm):
        FarmFollowFactory(follower_farm=user_with_farm.farm, followed_farm=other_farm)
        client.force_login(user_with_farm)
        response = client.get(reverse("farms:list"))
        farms = {f.pk: f for f in response.context["farms"]}
        assert farms[other_farm.pk].is_following is True
        assert farms[user_with_farm.farm.pk].is_following is False


class TestFarmProductListView:
    def test_unauthenticated_redirects(self, client, db):
        response = client.get(reverse("farms:product_list"))
        assert response.status_code == 302

    def test_authenticated_returns_200(self, client, user_with_farm):
        client.force_login(user_with_farm)
        response = client.get(reverse("farms:product_list"))
        assert response.status_code == 200

    def test_shows_only_own_products(self, client, user_with_farm, other_farm):
        own = FarmProductFactory(farm=user_with_farm.farm)
        other = FarmProductFactory(farm=other_farm)
        client.force_login(user_with_farm)
        response = client.get(reverse("farms:product_list"))
        pks = [p.pk for p in response.context["products"]]
        assert own.pk in pks
        assert other.pk not in pks


class TestFarmProductCreateView:
    def test_unauthenticated_redirects(self, client, db):
        response = client.get(reverse("farms:product_create"))
        assert response.status_code == 302

    def test_get_returns_200(self, client, user_with_farm):
        client.force_login(user_with_farm)
        response = client.get(reverse("farms:product_create"))
        assert response.status_code == 200

    def test_post_creates_product_for_own_farm(self, client, user_with_farm):
        from apps.farms.models import FarmProduct
        from apps.farms.tests.factories import CropCategoryFactory
        category = CropCategoryFactory()
        client.force_login(user_with_farm)
        response = client.post(
            reverse("farms:product_create"),
            {
                "name": "Tomates cerises",
                "crop_category": category.pk,
                "description": "",
                "default_unit": "kg",
                "default_price": "4.00",
                "is_active": True,
            },
        )
        assert response.status_code == 302
        assert FarmProduct.objects.filter(farm=user_with_farm.farm, name="Tomates cerises").exists()


class TestFarmProductUpdateView:
    def test_owner_can_access(self, client, user_with_farm):
        product = FarmProductFactory(farm=user_with_farm.farm)
        client.force_login(user_with_farm)
        response = client.get(reverse("farms:product_update", kwargs={"pk": product.pk}))
        assert response.status_code == 200

    def test_non_owner_gets_403(self, client, user_with_farm, other_farm):
        product = FarmProductFactory(farm=other_farm)
        client.force_login(user_with_farm)
        response = client.get(reverse("farms:product_update", kwargs={"pk": product.pk}))
        assert response.status_code == 403


class TestFarmProductDeleteView:
    def test_owner_can_delete(self, client, user_with_farm):
        from apps.farms.models import FarmProduct
        product = FarmProductFactory(farm=user_with_farm.farm)
        client.force_login(user_with_farm)
        response = client.post(reverse("farms:product_delete", kwargs={"pk": product.pk}))
        assert response.status_code == 302
        assert not FarmProduct.objects.filter(pk=product.pk).exists()

    def test_non_owner_gets_403(self, client, user_with_farm, other_farm):
        product = FarmProductFactory(farm=other_farm)
        client.force_login(user_with_farm)
        response = client.post(reverse("farms:product_delete", kwargs={"pk": product.pk}))
        assert response.status_code == 403
