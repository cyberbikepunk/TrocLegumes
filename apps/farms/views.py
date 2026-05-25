import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView, View

from .forms import FarmForm, FarmProductForm
from .models import Farm, FarmFollow, FarmProduct
from .utils import haversine_km

logger = logging.getLogger(__name__)


class FarmListView(ListView):
    model = Farm
    template_name = "farms/farm_list.html"
    context_object_name = "farms"
    queryset = Farm.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        farms = list(context["farms"])
        user = self.request.user
        if (
            user.is_authenticated
            and user.farm_id
            and user.farm.latitude is not None
            and user.farm.longitude is not None
        ):
            lat0, lon0 = user.farm.latitude, user.farm.longitude
            for farm in farms:
                if farm.latitude is not None and farm.longitude is not None:
                    farm.distance_km = round(haversine_km(lat0, lon0, farm.latitude, farm.longitude), 1)
                else:
                    farm.distance_km = None
            farms.sort(key=lambda f: (f.distance_km is None, f.distance_km or 0))
            context["user_has_location"] = True
        else:
            for farm in farms:
                farm.distance_km = None
            context["user_has_location"] = False
        context["farms"] = farms
        if user.is_authenticated and user.farm_id:
            following_pks = set(
                FarmFollow.objects.filter(follower_farm_id=user.farm_id)
                .values_list("followed_farm_id", flat=True)
            )
            for farm in farms:
                farm.is_following = farm.pk in following_pks
            context["can_follow"] = True
        else:
            for farm in farms:
                farm.is_following = False
            context["can_follow"] = False
        return context


class FarmDetailView(DetailView):
    model = Farm
    template_name = "farms/farm_detail.html"
    context_object_name = "farm"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        farm = self.object
        context["is_own_farm"] = user.is_authenticated and user.farm_id == farm.pk
        context["can_follow"] = (
            user.is_authenticated
            and user.farm is not None
            and user.farm_id != farm.pk
        )
        context["is_following"] = context["can_follow"] and FarmFollow.objects.filter(
            follower_farm_id=user.farm_id, followed_farm=farm
        ).exists()
        context["followers_count"] = farm.followers.count()
        context["products"] = farm.products.filter(is_active=True).select_related("crop_category")
        if farm.latitude and farm.longitude:
            context["farm_lat"] = float(farm.latitude)
            context["farm_lon"] = float(farm.longitude)
        return context


class FarmCreateView(LoginRequiredMixin, CreateView):
    model = Farm
    form_class = FarmForm
    template_name = "farms/farm_form.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.farm_id:
            return redirect("farms:detail", pk=request.user.farm_id)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        farm = form.save()
        self.request.user.farm = farm
        self.request.user.save(update_fields=["farm"])
        logger.info("Farm %d '%s' created by user %d", farm.pk, farm.name, self.request.user.pk)
        messages.success(self.request, f"Votre ferme « {farm.name} » a été créée.")
        return redirect("farms:detail", pk=farm.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["action"] = "Créer ma ferme"
        return context


class FarmUpdateView(LoginRequiredMixin, UpdateView):
    model = Farm
    form_class = FarmForm
    template_name = "farms/farm_form.html"

    def get_object(self, queryset=None):
        farm = super().get_object(queryset)
        if self.request.user.farm_id != farm.pk:
            raise PermissionDenied
        return farm

    def get_success_url(self):
        return reverse("farms:detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        response = super().form_valid(form)
        logger.info("Farm %d updated by user %d", self.object.pk, self.request.user.pk)
        messages.success(self.request, "Votre ferme a été mise à jour.")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["action"] = "Modifier ma ferme"
        return context


class FollowToggleView(LoginRequiredMixin, View):
    def post(self, request, pk):
        followed_farm = get_object_or_404(Farm, pk=pk)
        follower_farm = request.user.farm

        if follower_farm is None or follower_farm.pk == followed_farm.pk:
            return self._render_button(request, followed_farm, is_following=False, can_follow=False)

        follow_qs = FarmFollow.objects.filter(follower_farm=follower_farm, followed_farm=followed_farm)
        if follow_qs.exists():
            follow_qs.delete()
            is_following = False
            logger.info("Farm %d unfollowed farm %d", follower_farm.pk, followed_farm.pk)
        else:
            FarmFollow.objects.create(follower_farm=follower_farm, followed_farm=followed_farm)
            is_following = True
            logger.info("Farm %d followed farm %d", follower_farm.pk, followed_farm.pk)

        return self._render_button(request, followed_farm, is_following=is_following, can_follow=True)

    def _render_button(self, request, farm, is_following, can_follow):
        html = render_to_string(
            "farms/partials/follow_button.html",
            {"farm": farm, "is_following": is_following, "can_follow": can_follow},
            request=request,
        )
        return HttpResponse(html)


class FarmProductListView(LoginRequiredMixin, ListView):
    model = FarmProduct
    template_name = "farms/farm_product_list.html"
    context_object_name = "products"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.farm_id:
            messages.warning(request, "Vous devez d'abord créer votre ferme.")
            return redirect("farms:create")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return FarmProduct.objects.filter(farm=self.request.user.farm).select_related("crop_category")


class FarmProductCreateView(LoginRequiredMixin, CreateView):
    model = FarmProduct
    form_class = FarmProductForm
    template_name = "farms/farm_product_form.html"
    success_url = reverse_lazy("farms:product_list")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.farm_id:
            messages.warning(request, "Vous devez d'abord créer votre ferme.")
            return redirect("farms:create")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        product = form.save(commit=False)
        product.farm = self.request.user.farm
        product.save()
        logger.info("FarmProduct %d '%s' created by user %d", product.pk, product.name, self.request.user.pk)
        messages.success(self.request, f"Le produit « {product.name} » a été ajouté.")
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["action"] = "Ajouter un produit"
        return context


class FarmProductUpdateView(LoginRequiredMixin, UpdateView):
    model = FarmProduct
    form_class = FarmProductForm
    template_name = "farms/farm_product_form.html"
    success_url = reverse_lazy("farms:product_list")

    def get_object(self, queryset=None):
        product = super().get_object(queryset)
        if product.farm_id != self.request.user.farm_id:
            raise PermissionDenied
        return product

    def form_valid(self, form):
        response = super().form_valid(form)
        logger.info("FarmProduct %d updated by user %d", self.object.pk, self.request.user.pk)
        messages.success(self.request, f"Le produit « {self.object.name} » a été mis à jour.")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["action"] = "Modifier le produit"
        return context


class FarmProductDeleteView(LoginRequiredMixin, DeleteView):
    model = FarmProduct
    template_name = "farms/farm_product_confirm_delete.html"
    success_url = reverse_lazy("farms:product_list")

    def get_object(self, queryset=None):
        product = super().get_object(queryset)
        if product.farm_id != self.request.user.farm_id:
            raise PermissionDenied
        return product

    def form_valid(self, form):
        logger.info("FarmProduct %d deleted by user %d", self.object.pk, self.request.user.pk)
        messages.success(self.request, f"Le produit « {self.object.name} » a été supprimé.")
        return super().form_valid(form)
