import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView

from apps.farms.models import FarmFollow

from .forms import ListingForm
from .models import Listing, Week

logger = logging.getLogger(__name__)


def _get_active_week():
    return Week.objects.filter(is_active=True).first()


class MarketplaceView(TemplateView):
    template_name = "market/marketplace.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        active_week = _get_active_week()
        context["active_week"] = active_week

        if not active_week:
            context["listings"] = []
            return context

        listings = (
            Listing.objects.filter(week=active_week, is_active=True)
            .select_related("farm_product", "farm_product__crop_category", "farm")
            .order_by("farm__name", "farm_product__name")
        )

        user = self.request.user
        if user.is_authenticated and user.farm_id:
            followed_pks = set(
                FarmFollow.objects.filter(follower_farm_id=user.farm_id)
                .values_list("followed_farm_id", flat=True)
            )
            # Followed farms first, then others; exclude own farm's listings from "others"
            followed = [lst for lst in listings if lst.farm_id in followed_pks]
            others = [lst for lst in listings if lst.farm_id not in followed_pks and lst.farm_id != user.farm_id]
            own = [lst for lst in listings if lst.farm_id == user.farm_id]
            context["listings_followed"] = followed
            context["listings_others"] = others
            context["listings_own"] = own
        else:
            context["listings_followed"] = []
            context["listings_others"] = list(listings)
            context["listings_own"] = []

        return context


class _ListingOwnerMixin:
    """Ensure the listing belongs to the current user's farm."""

    def get_object(self, queryset=None):
        listing = super().get_object(queryset)
        if listing.farm_id != self.request.user.farm_id:
            raise PermissionDenied
        return listing


class ListingListView(LoginRequiredMixin, ListView):
    model = Listing
    template_name = "market/listing_list.html"
    context_object_name = "listings"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.farm_id:
            messages.warning(request, "Vous devez d'abord créer votre ferme.")
            return redirect("farms:create")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return (
            Listing.objects.filter(farm=self.request.user.farm)
            .select_related("farm_product", "farm_product__crop_category", "week")
            .order_by("-week__start_date", "farm_product__name")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_week"] = _get_active_week()
        return context


class ListingCreateView(LoginRequiredMixin, CreateView):
    model = Listing
    form_class = ListingForm
    template_name = "market/listing_form.html"
    success_url = reverse_lazy("market:listing_list")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.farm_id:
            messages.warning(request, "Vous devez d'abord créer votre ferme.")
            return redirect("farms:create")
        self.active_week = _get_active_week()
        if request.user.is_authenticated and not self.active_week:
            messages.warning(request, "Aucune semaine active en ce moment. Revenez plus tard.")
            return redirect("market:listing_list")
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["farm"] = self.request.user.farm
        return kwargs

    def form_valid(self, form):
        listing = form.save(commit=False)
        listing.farm = self.request.user.farm
        listing.week = self.active_week
        listing.save()
        logger.info(
            "Listing %d created by farm %d for week %d",
            listing.pk, listing.farm_id, listing.week_id,
        )
        messages.success(self.request, f"L'annonce pour « {listing.farm_product.name} » a été créée.")
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["action"] = "Nouvelle annonce"
        context["active_week"] = self.active_week
        return context


class ListingUpdateView(LoginRequiredMixin, _ListingOwnerMixin, UpdateView):
    model = Listing
    form_class = ListingForm
    template_name = "market/listing_form.html"
    success_url = reverse_lazy("market:listing_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["farm"] = self.request.user.farm
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        logger.info("Listing %d updated by farm %d", self.object.pk, self.request.user.farm_id)
        messages.success(self.request, f"L'annonce pour « {self.object.farm_product.name} » a été mise à jour.")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["action"] = "Modifier l'annonce"
        context["active_week"] = self.object.week
        return context


class ListingDeleteView(LoginRequiredMixin, _ListingOwnerMixin, DeleteView):
    model = Listing
    template_name = "market/listing_confirm_delete.html"
    success_url = reverse_lazy("market:listing_list")

    def form_valid(self, form):
        logger.info("Listing %d deleted by farm %d", self.object.pk, self.request.user.farm_id)
        messages.success(self.request, f"L'annonce pour « {self.object.farm_product.name} » a été supprimée.")
        return super().form_valid(form)
