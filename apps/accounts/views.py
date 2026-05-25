import json

from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, TemplateView

from apps.farms.constants import MAP_RADIUS_KM
from apps.farms.models import Farm, FarmFollow
from apps.farms.utils import haversine_km

from .forms import LoginForm, RegistrationForm


class CustomLoginView(LoginView):
    form_class = LoginForm
    template_name = "accounts/login.html"

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("dashboard")
        return super().get(request, *args, **kwargs)


class RegisterView(CreateView):
    form_class = RegistrationForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("dashboard")

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("dashboard")
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect("farms:create")


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.farm:
            context["followed_farms"] = (
                FarmFollow.objects
                .filter(follower_farm=user.farm)
                .select_related("followed_farm")
                .order_by("followed_farm__name")
            )
        else:
            context["followed_farms"] = []

        farms_with_coords = list(
            Farm.objects.filter(is_active=True, latitude__isnull=False, longitude__isnull=False)
        )
        if user.farm and user.farm.latitude and user.farm.longitude:
            lat0, lon0 = float(user.farm.latitude), float(user.farm.longitude)
            followed_pks = set(
                FarmFollow.objects.filter(follower_farm=user.farm)
                .values_list("followed_farm_id", flat=True)
            )
            nearby_pks = {
                f.pk for f in farms_with_coords
                if haversine_km(lat0, lon0, f.latitude, f.longitude) <= MAP_RADIUS_KM
            }
            all_pks = nearby_pks | (followed_pks & {f.pk for f in farms_with_coords})
            all_map_farms = [f for f in farms_with_coords if f.pk in all_pks]
            context["map_farms"] = all_map_farms
            context["map_farms_json"] = json.dumps([
                {"lat": float(f.latitude), "lng": float(f.longitude), "name": f.name,
                 "url": reverse("farms:detail", args=[f.pk]),
                 "followed": f.pk in followed_pks}
                for f in all_map_farms
            ])
            context["map_center_json"] = json.dumps([lat0, lon0])
            context["map_zoom"] = 9
        else:
            context["map_farms"] = farms_with_coords
            context["map_farms_json"] = json.dumps([
                {"lat": float(f.latitude), "lng": float(f.longitude), "name": f.name,
                 "url": reverse("farms:detail", args=[f.pk])}
                for f in farms_with_coords
            ])
            context["map_center_json"] = "null"
            context["map_zoom"] = 6

        return context
