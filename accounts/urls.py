from django.urls import path
from . import views
from django.http import HttpResponse


def home_view(request):
    return HttpResponse("ログイン成功！")


urlpatterns = [
    path("", views.login_view, name="login"),
    path("signup/", views.signup_view, name="signup"),
    path("home/", views.home_view, name="home"),
    path("products/search/", views.product_search, name="product_search"),
]