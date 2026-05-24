from django.contrib.auth.views import LogoutView
from django.urls import path

from .views import CustomLoginView, RegisterView

app_name = "accounts"

urlpatterns = [
    path("connexion/", CustomLoginView.as_view(), name="login"),
    path("deconnexion/", LogoutView.as_view(), name="logout"),
    path("inscription/", RegisterView.as_view(), name="register"),
]
