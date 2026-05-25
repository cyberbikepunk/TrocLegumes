from django.urls import path

from .views import ListingCreateView, ListingDeleteView, ListingListView, ListingUpdateView, MarketplaceView

app_name = "market"

urlpatterns = [
    path("", MarketplaceView.as_view(), name="marketplace"),
    path("mes-annonces/", ListingListView.as_view(), name="listing_list"),
    path("mes-annonces/nouvelle/", ListingCreateView.as_view(), name="listing_create"),
    path("mes-annonces/<int:pk>/modifier/", ListingUpdateView.as_view(), name="listing_update"),
    path("mes-annonces/<int:pk>/supprimer/", ListingDeleteView.as_view(), name="listing_delete"),
]
