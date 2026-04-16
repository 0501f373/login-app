from django.urls import path
from . import views

urlpatterns = [
    path("", views.product_search, name="product_search"),
    path("login/", views.login_view, name="login"),
    path("signup/", views.signup_view, name="signup"),
    path("logout/", views.logout_view, name="logout"),

    path("products/<int:product_id>/", views.product_detail, name="product_detail"),
    path("cart/add/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path("cart/", views.cart_view, name="cart"),
    path("order/confirm/", views.order_confirm, name="order_confirm"),
    path("cart/remove/<int:product_id>/", views.remove_from_cart, name="remove_from_cart"),
    path("cart/update/<int:product_id>/", views.update_cart, name="update_cart"),

    path("staff/login/", views.staff_login_view, name="staff_login"),
    path("management/", views.management_menu, name="management_menu"),
    path("management/products/", views.product_edit_menu, name="product_edit_menu"),
    path("management/products/add/", views.product_create, name="product_create"),
    path("management/products/<int:product_id>/edit/", views.product_edit, name="product_edit"),
    path("management/products/<int:product_id>/delete/", views.product_delete, name="product_delete"),
    path("management/categories/add/", views.category_create, name="category_create"),
    path("management/manufacturers/add/", views.manufacturer_create, name="manufacturer_create"),
    path("staff/logout/", views.staff_logout_view, name="staff_logout"),
    path("management/products/view/", views.management_product_list, name="management_product_list"),
    path("management/staff/create/", views.staff_signup_view, name="staff_signup"),
    path("management/staff/", views.staff_list_view, name="staff_list"),
]