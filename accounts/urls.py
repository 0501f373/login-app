from django.urls import path
from . import views

urlpatterns = [
    path("", views.product_search, name="product_search"),  # ←トップを検索に
    path("login/", views.login_view, name="login"),
    path("signup/", views.signup_view, name="signup"),
    path("home/", views.home_view, name="home"),
    path("products/<int:product_id>/", views.product_detail, name="product_detail"),
    path("cart/add/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path("cart/", views.cart_view, name="cart"),
    path("order/confirm/", views.order_confirm, name="order_confirm"),
    path("cart/remove/<int:product_id>/", views.remove_from_cart, name="remove_from_cart"),
]