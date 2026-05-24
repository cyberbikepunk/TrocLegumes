import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.generic import CreateView, DetailView, ListView, UpdateView, View

from .forms import FarmForm
from .models import Farm, FarmFollow

logger = logging.getLogger(__name__)


class FarmListView(ListView):
    model = Farm
    template_name = "farms/farm_list.html"
    context_object_name = "farms"
    queryset = Farm.objects.filter(is_active=True)


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
