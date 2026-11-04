from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("github/", views.github_guide, name="github_guide"),
    path("product/<slug:slug>/", views.product_detail, name="product_detail"),
    path("register/", views.register_page, name="register"),
    path("verify-code/", views.verify_code_page, name="verify_code"),
    path("resend-verification/", views.resend_verification_page, name="resend_verification"),
    path("account/email/", views.change_email_page, name="change_email"),
    path("account/email/verify/", views.verify_email_change_page, name="verify_email_change"),
    path("account/profile/", views.profile_page, name="profile"),
    path("login/", views.login_page, name="login"),
    path("password-reset/", views.password_reset_request_page, name="password_reset_request"),
    path("password-reset/verify/", views.password_reset_verify_page, name="password_reset_verify"),
    path("auth/<str:provider>/", views.social_login_start, name="social_login_start"),
    path("cart/", views.cart_page, name="cart"),
    path("checkout/", views.checkout_page, name="checkout"),
    path("logout/", views.logout_page, name="logout"),
]
