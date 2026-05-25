from django.urls import path

from .views import (
    FarmCreateView,
    FarmDetailView,
    FarmListView,
    FarmProductCreateView,
    FarmProductDeleteView,
    FarmProductListView,
    FarmProductUpdateView,
    FarmUpdateView,
    FollowToggleView,
)

app_name = "farms"

urlpatterns = [
    path("", FarmListView.as_view(), name="list"),
    path("nouvelle/", FarmCreateView.as_view(), name="create"),
    path("<int:pk>/", FarmDetailView.as_view(), name="detail"),
    path("<int:pk>/modifier/", FarmUpdateView.as_view(), name="update"),
    path("<int:pk>/suivre/", FollowToggleView.as_view(), name="follow_toggle"),
    # Products
    path("mes-produits/", FarmProductListView.as_view(), name="product_list"),
    path("mes-produits/nouveau/", FarmProductCreateView.as_view(), name="product_create"),
    path("mes-produits/<int:pk>/modifier/", FarmProductUpdateView.as_view(), name="product_update"),
    path("mes-produits/<int:pk>/supprimer/", FarmProductDeleteView.as_view(), name="product_delete"),
]
