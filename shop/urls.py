from __future__ import annotations

from django.contrib.auth import views as auth_views
from django.urls import path

from shop import views

urlpatterns = [
    path("", views.index, name="index"),
    path("accounts/signup/", views.signup, name="signup"),
    path("accounts/login/", auth_views.LoginView.as_view(), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),

    path("products/add/", views.ProductCreateView.as_view(), name="product_add"),
    path("product/<slug:slug>/edit/", views.ProductUpdateView.as_view(), name="product_edit"),
    path(
        "product/<slug:slug>/delete/",
        views.ProductDeleteView.as_view(),
        name="product_delete",
    ),
    path("product/<slug:slug>/", views.product_detail, name="product_detail"),
    path("cart/", views.cart_detail, name="cart"),
    path("cart/add/<int:product_id>/", views.cart_add_view, name="cart_add"),
    path("cart/remove/<int:product_id>/", views.cart_remove_view, name="cart_remove"),
    path("checkout/", views.checkout, name="checkout"),
    path(
        "checkout/success/<int:order_id>/",
        views.checkout_success,
        name="checkout_success",
    ),
]

