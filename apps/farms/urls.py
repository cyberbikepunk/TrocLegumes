from django.urls import path

from .views import FarmCreateView, FarmDetailView, FarmListView, FarmUpdateView, FollowToggleView

app_name = "farms"

urlpatterns = [
    path("", FarmListView.as_view(), name="list"),
    path("nouvelle/", FarmCreateView.as_view(), name="create"),
    path("<int:pk>/", FarmDetailView.as_view(), name="detail"),
    path("<int:pk>/modifier/", FarmUpdateView.as_view(), name="update"),
    path("<int:pk>/suivre/", FollowToggleView.as_view(), name="follow_toggle"),
]
