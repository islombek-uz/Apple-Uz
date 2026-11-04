import json
from io import BytesIO
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from .models import Order, OrderItem, Product, Profile, get_profile_for_user


class StorefrontTests(TestCase):
    def test_guest_nav_shows_default_avatar_linked_to_login(self):
        response = self.client.get(reverse("home"))

        self.assertContains(response, 'class="nav-profile-link"')
        self.assertContains(response, 'href="/login/" aria-label="Hisobga kirish"')
        self.assertContains(response, "avatar-default.svg")

    def test_guest_homepage_shows_public_storefront(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sevimli texnologiyangiz shu yerdan boshlanadi.")
        self.assertContains(response, "MacBook Air")
        self.assertContains(response, "/product/iphone-17-pro/")

    def test_github_guide_page_is_available_and_interactive(self):
        response = self.client.get(reverse("github_guide"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Git & <span>GitHub</span>")
        self.assertContains(response, "function copyCode(btn)")
        self.assertContains(response, 'id="pull-request"')

    def test_guest_can_open_cart_page(self):
        response = self.client.get(reverse("cart"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Savat")
        self.assertContains(response, 'action="/checkout/"')

    def test_logout_notice_has_dismissible_toast_markup(self):
        self.client.get(reverse("logout"))

        response = self.client.get(reverse("home"))

        self.assertContains(response, "site-notice--info")
        self.assertContains(response, 'aria-label="Xabarni yopish"')

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.console.EmailBackend")
    def test_password_reset_page_explains_console_email_delivery(self):
        response = self.client.get(reverse("password_reset_request"))

        self.assertContains(response, "sinov kodi server terminalida ko‘rinadi")

    def test_inactive_account_can_request_another_verification_code(self):
        user = get_user_model().objects.create_user(
            username="resend-inactive-user",
            email="resend-inactive@example.com",
            password="Strong-Apple-Password-874!",
            is_active=False,
        )

        response = self.client.post(
            reverse("resend_verification"), {"email": user.email}
        )

        self.assertRedirects(response, reverse("verify_code"))
        self.assertEqual(self.client.session.get("verify_email"), user.email)
        profile = get_profile_for_user(user)
        self.assertRegex(profile.activation_code, r"^\d{6}$")
        self.assertEqual(mail.outbox[-1].to, [user.email])

    def test_guest_can_create_order_with_catalog_price(self):
        product = Product.objects.get(slug="ipad-pro")

        response = self.client.post(
            reverse("checkout"),
            {
                "first_name": "Test",
                "last_name": "Customer",
                "email": "buyer@example.com",
                "phone": "+998901234567",
                "address": "Toshkent",
                "payment_method": "cash",
                "notes": "",
                "cart_items": json.dumps(
                    [{"id": product.pk, "quantity": 2, "price": 1}]
                ),
            },
        )

        self.assertRedirects(response, reverse("cart"))
        order = Order.objects.get(email="buyer@example.com")
        item = OrderItem.objects.get(order=order)
        self.assertEqual(order.total_price, product.price * 2)
        self.assertEqual(item.product_price, product.price)
        self.assertEqual(item.quantity, 2)
        self.assertIsNone(order.user)

    def test_checkout_rejects_invalid_product_and_quantity(self):
        for item_data in ('[{"id": 999999, "quantity": 1}]', '[{"id": 1, "quantity": 0}]'):
            response = self.client.post(
                reverse("checkout"),
                {
                    "first_name": "Test",
                    "email": "buyer@example.com",
                    "phone": "+998901234567",
                    "payment_method": "cash",
                    "cart_items": item_data,
                },
            )
            self.assertEqual(response.status_code, 400)
        self.assertEqual(Order.objects.count(), 0)

    def test_authenticated_homepage_shows_filterable_catalog(self):
        user = get_user_model().objects.create_user("catalog-user", password="test-pass-123")
        self.client.force_login(user)

        response = self.client.get(reverse("home"), {"category": "mac"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "MacBook Air")
        self.assertNotContains(response, "iPhone 17 Pro")
        self.assertContains(response, "images.unsplash.com")

    def test_product_detail_page(self):
        user = get_user_model().objects.create_user("detail-user", password="test-pass-123")
        self.client.force_login(user)

        response = self.client.get(reverse("product_detail", args=["ipad-pro"]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "iPad Pro")
        self.assertContains(response, "12 999 000")
        self.assertContains(response, "specification-table")
        self.assertContains(response, "images.unsplash.com")

    def test_product_detail_requires_login(self):
        response = self.client.get(reverse("product_detail", args=["ipad-pro"]))

        self.assertRedirects(response, f"{reverse('login')}?next={reverse('product_detail', args=['ipad-pro'])}")

    def test_unknown_product_returns_404(self):
        user = get_user_model().objects.create_user("missing-user", password="test-pass-123")
        self.client.force_login(user)

        response = self.client.get(reverse("product_detail", args=["unknown-product"]))

        self.assertEqual(response.status_code, 404)

    def test_admin_can_manage_products(self):
        admin_user = get_user_model().objects.create_superuser(
            "storeadmin", "admin@example.com", "test-pass-123"
        )
        self.client.force_login(admin_user)

        response = self.client.get(reverse("admin:store_product_changelist"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "iPhone 17 Pro")


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class AccountTests(TestCase):
    def test_user_can_have_multiple_profiles_but_app_uses_first(self):
        user = get_user_model().objects.create_user(
            username="multiple-profile-user", password="test-pass-123"
        )
        first_profile = Profile.objects.create(user=user)
        second_profile = Profile.objects.create(user=user)

        self.assertEqual(Profile.objects.filter(user=user).count(), 2)
        self.assertEqual(get_profile_for_user(user).pk, first_profile.pk)
        self.assertNotEqual(first_profile.pk, second_profile.pk)

    @patch("store.models.send_telegram_message")
    def test_registration_notifies_admin_on_site_signup(self, mock_send):
        user = get_user_model().objects.create_user(
            username="notify-admin-user",
            email="notify-admin@example.com",
            password="test-pass-123",
        )

        self.assertTrue(user.pk)
        mock_send.assert_called_once()
        args = mock_send.call_args.args
        self.assertEqual(args[0], "8803005871")
        self.assertIn("Yangi foydalanuvchi ro'yxatdan o'tdi", args[1])

    def test_profile_page_shows_fallback_and_saves_uploaded_avatar(self):
        user = get_user_model().objects.create_user(
            username="profile-customer",
            email="profile@example.com",
            password="test-pass-123",
        )
        self.client.force_login(user)

        with TemporaryDirectory() as media_dir, override_settings(MEDIA_ROOT=media_dir):
            response = self.client.get(reverse("profile"))

            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "avatar-default.svg")
            self.assertContains(response, 'class="nav-profile-link"')
            self.assertContains(response, "Emailni o‘zgartirish")

            image_data = BytesIO()
            Image.new("RGB", (2, 2), "white").save(image_data, format="PNG")
            image_data.seek(0)
            response = self.client.post(
                reverse("profile"),
                {
                    "avatar": SimpleUploadedFile(
                        "avatar.png", image_data.read(), content_type="image/png"
                    )
                },
            )

            self.assertRedirects(response, reverse("profile"))
            profile = get_profile_for_user(user)
            profile.refresh_from_db()
            self.assertTrue(profile.avatar.name.startswith("avatars/"))
            response = self.client.get(reverse("profile"))
            self.assertContains(response, profile.avatar.url)

    def test_profile_form_renders_the_correct_field_labels(self):
        user = get_user_model().objects.create_user(
            username="profile-labels", email="labels@example.com", password="test-pass-123"
        )
        self.client.force_login(user)

        response = self.client.get(reverse("profile"))

        self.assertContains(response, 'for="id_first_name">Ism</label>')
        self.assertContains(response, 'for="id_phone">Telefon raqami</label>')
        self.assertNotContains(response, 'for="id_phone">Profil rasmi</label>')

    def test_profile_page_requires_login(self):
        response = self.client.get(reverse("profile"))

        self.assertRedirects(response, f"{reverse('login')}?next={reverse('profile')}")

    def test_email_change_page_is_available_to_authenticated_users(self):
        user = get_user_model().objects.create_user(
            username="email-change-user",
            email="old@example.com",
            password="test-pass-123",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("change_email"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Yangi email manzilingizni kiriting")

    def test_email_change_sends_code_without_changing_email(self):
        user = get_user_model().objects.create_user(
            username="email-change-customer",
            email="old@example.com",
            password="test-pass-123",
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("change_email"), {"email": "new@example.com"}
        )

        self.assertRedirects(response, reverse("verify_email_change"))
        user.refresh_from_db()
        self.assertEqual(user.email, "old@example.com")
        profile = get_profile_for_user(user)
        self.assertRegex(profile.activation_code, r"^\d{6}$")
        self.assertEqual(mail.outbox[-1].to, ["new@example.com"])

    def test_email_change_updates_address_after_valid_code(self):
        user = get_user_model().objects.create_user(
            username="email-verify-customer",
            email="old-verify@example.com",
            password="test-pass-123",
        )
        self.client.force_login(user)
        profile = Profile.objects.create(
            user=user,
            activation_code="123456",
            code_created_at=timezone.now(),
        )
        session = self.client.session
        session["pending_email"] = "new-verify@example.com"
        session["email_change_user_id"] = user.pk
        session.save()

        response = self.client.post(
            reverse("verify_email_change"), {"code": "123456"}
        )

        self.assertRedirects(response, reverse("profile"))
        user.refresh_from_db()
        profile.refresh_from_db()
        self.assertEqual(user.email, "new-verify@example.com")
        self.assertEqual(profile.activation_code, "")

    def test_registration_page_has_localized_help_text(self):
        response = self.client.get(reverse("register"))

        self.assertContains(response, "150 belgigacha")
        self.assertContains(response, "Kamida 8 belgi")
        self.assertNotContains(response, "Your password")

    def test_registration_sends_code_and_keeps_account_inactive(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "new-customer",
                "email": "customer@example.com",
                "password1": "Strong-Apple-Password-874!",
                "password2": "Strong-Apple-Password-874!",
            },
        )

        self.assertRedirects(response, reverse("verify_code"))
        user = get_user_model().objects.get(username="new-customer")
        self.assertFalse(user.is_active)
        profile = get_profile_for_user(user)
        self.assertRegex(profile.activation_code, r"^\d{6}$")
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(profile.activation_code, mail.outbox[0].body)

    def test_verification_activates_and_logs_in_user(self):
        user = get_user_model().objects.create_user(
            username="waiting-customer",
            email="waiting@example.com",
            password="Strong-Apple-Password-874!",
            is_active=False,
        )
        Profile.objects.create(
            user=user,
            activation_code="123456",
            code_created_at=timezone.now(),
        )
        session = self.client.session
        session["verify_email"] = user.email
        session.save()

        response = self.client.post(reverse("verify_code"), {"code": "123456"})

        self.assertRedirects(response, reverse("home"))
        user.refresh_from_db()
        profile = get_profile_for_user(user)
        profile.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertEqual(profile.activation_code, "")
        self.assertIn("_auth_user_id", self.client.session)

    def test_login_accepts_email_address(self):
        user = get_user_model().objects.create_user(
            username="email-customer",
            email="email@example.com",
            password="Strong-Apple-Password-874!",
            is_active=True,
        )

        response = self.client.post(
            reverse("login"),
            {"username": "EMAIL@example.com", "password": "Strong-Apple-Password-874!"},
        )

        self.assertRedirects(response, reverse("home"))
        self.assertEqual(self.client.session.get("_auth_user_id"), str(user.pk))

    def test_login_page_links_to_password_reset(self):
        response = self.client.get(reverse("login"))

        self.assertContains(response, "Parolni unutdingizmi?")
        self.assertContains(response, reverse("password_reset_request"))

    def test_password_reset_sends_code_and_does_not_reveal_unknown_email(self):
        user = get_user_model().objects.create_user(
            username="password-reset-customer",
            email="reset@example.com",
            password="Old-Strong-Password-874!",
        )

        response = self.client.post(
            reverse("password_reset_request"), {"email": user.email}
        )

        self.assertRedirects(response, reverse("password_reset_verify"))
        user.refresh_from_db()
        profile = get_profile_for_user(user)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [user.email])
        self.assertIn(profile.activation_code, mail.outbox[0].body)

        unknown_response = self.client.post(
            reverse("password_reset_request"), {"email": "missing@example.com"}
        )
        self.assertRedirects(unknown_response, reverse("password_reset_verify"))
        self.assertEqual(len(mail.outbox), 1)

    def test_password_reset_requires_valid_email_code_then_updates_password(self):
        user = get_user_model().objects.create_user(
            username="reset-password-user",
            email="reset-password@example.com",
            password="Old-Strong-Password-874!",
        )
        profile = Profile.objects.create(
            user=user,
            activation_code="123456",
            code_created_at=timezone.now(),
        )
        session = self.client.session
        session["password_reset_email"] = user.email
        session.save()

        response = self.client.post(
            reverse("password_reset_verify"),
            {
                "code": "000000",
                "new_password1": "New-Strong-Password-965!",
                "new_password2": "New-Strong-Password-965!",
            },
        )
        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.check_password("Old-Strong-Password-874!"))
        profile.refresh_from_db()
        self.assertEqual(profile.code_attempts, 1)

        response = self.client.post(
            reverse("password_reset_verify"),
            {
                "code": "123456",
                "new_password1": "New-Strong-Password-965!",
                "new_password2": "New-Strong-Password-965!",
            },
        )
        self.assertRedirects(response, reverse("login"))
        user.refresh_from_db()
        profile.refresh_from_db()
        self.assertTrue(user.check_password("New-Strong-Password-965!"))
        self.assertEqual(profile.activation_code, "")
        self.assertNotIn("password_reset_email", self.client.session)

    def test_verification_code_can_be_resent(self):
        user = get_user_model().objects.create_user(
            username="resend-customer",
            email="resend@example.com",
            password="Strong-Apple-Password-874!",
            is_active=False,
        )
        profile = Profile.objects.create(user=user)
        session = self.client.session
        session["verify_email"] = user.email
        session.save()

        response = self.client.post(reverse("verify_code"), {"action": "resend"})

        self.assertEqual(response.status_code, 200)
        profile.refresh_from_db()
        self.assertRegex(profile.activation_code, r"^\d{6}$")
        self.assertEqual(len(mail.outbox), 1)

    def test_failed_resend_keeps_previous_verification_code(self):
        user = get_user_model().objects.create_user(
            username="failed-resend-customer",
            email="failed-resend@example.com",
            password="Strong-Apple-Password-874!",
            is_active=False,
        )
        profile = Profile.objects.create(
            user=user,
            activation_code="123456",
            code_created_at=timezone.now(),
            code_attempts=2,
        )
        session = self.client.session
        session["verify_email"] = user.email
        session.save()

        with patch("store.views.send_mail", side_effect=OSError("SMTP unavailable")):
            response = self.client.post(reverse("verify_code"), {"action": "resend"})

        self.assertEqual(response.status_code, 200)
        profile.refresh_from_db()
        self.assertEqual(profile.activation_code, "123456")
        self.assertEqual(profile.code_attempts, 2)

    def test_verification_locks_code_after_five_wrong_attempts(self):
        user = get_user_model().objects.create_user(
            username="limited-customer",
            email="limited@example.com",
            password="Strong-Apple-Password-874!",
            is_active=False,
        )
        Profile.objects.create(
            user=user,
            activation_code="123456",
            code_created_at=timezone.now(),
        )
        session = self.client.session
        session["verify_email"] = user.email
        session.save()

        for _ in range(Profile.MAX_CODE_ATTEMPTS):
            self.client.post(reverse("verify_code"), {"code": "000000"})

        response = self.client.post(reverse("verify_code"), {"code": "123456"})

        profile = get_profile_for_user(user)
        profile.refresh_from_db()
        self.assertEqual(profile.code_attempts, Profile.MAX_CODE_ATTEMPTS)
        self.assertFalse(user.is_active)
        self.assertContains(response, "Urinishlar limiti tugadi")


class SocialLoginTests(TestCase):
    @override_settings(
        SOCIALACCOUNT_PROVIDERS={
            "google": {
                "APP": {
                    "client_id": "google-client-id",
                    "secret": "google-client-secret",
                    "key": "",
                },
                "SCOPE": ["profile", "email"],
                "AUTH_PARAMS": {"access_type": "online"},
                "OAUTH_PKCE_ENABLED": True,
            },
            "telegram": {
                "APP": {
                    "client_id": "123456789",
                    "secret": "123456789:telegram-token",
                    "key": "",
                },
            },
        }
    )
    def test_login_and_registration_pages_always_show_social_buttons(self):
        response = self.client.get(reverse("login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Google orqali davom etish")
        self.assertContains(response, "Telegram orqali davom etish")
        self.assertContains(response, f'action="{reverse("google_login")}?process=login"')
        self.assertContains(response, f'action="{reverse("telegram_login")}?process=login"')
        self.assertContains(response, 'name="csrfmiddlewaretoken"')

        register_response = self.client.get(reverse("register"))
        self.assertContains(register_response, "Google orqali davom etish")
        self.assertContains(register_response, "Telegram orqali davom etish")

    @override_settings(
        SOCIALACCOUNT_PROVIDERS={
            "google": {"APP": {"client_id": "", "secret": "", "key": ""}},
            "telegram": {
                "APP": {
                    "client_id": "123456789",
                    "secret": "123456789:telegram-token",
                    "key": "",
                }
            },
        }
    )
    def test_telegram_post_starts_auth_without_confirmation_page(self):
        response = self.client.post(f"{reverse('telegram_login')}?process=login")

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith("https://oauth.telegram.org/auth?"))

    @override_settings(
        SOCIALACCOUNT_PROVIDERS={
            "google": {
                "APP": {
                    "client_id": "google-client-id",
                    "secret": "google-client-secret",
                    "key": "",
                },
                "SCOPE": ["profile", "email"],
                "AUTH_PARAMS": {"access_type": "online"},
                "OAUTH_PKCE_ENABLED": True,
            },
            "telegram": {"APP": {"client_id": "", "secret": "", "key": ""}},
        }
    )
    def test_google_post_starts_oauth_without_confirmation_page(self):
        response = self.client.post(
            f"{reverse('google_login')}?process=login"
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("accounts.google.com", response["Location"])

    @override_settings(
        SOCIALACCOUNT_PROVIDERS={
            "google": {"APP": {"client_id": "", "secret": "", "key": ""}},
            "telegram": {"APP": {"client_id": "", "secret": "", "key": ""}},
        }
    )
    def test_missing_credentials_show_setup_instructions(self):
        response = self.client.get(
            reverse("social_login_start", args=["google"])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "GOOGLE_CLIENT_ID")
        self.assertContains(
            response,
            "http://testserver/accounts/google/login/callback/",
        )
        self.assertContains(response, "OAuth consent screen")

    @override_settings(
        SOCIALACCOUNT_PROVIDERS={
            "google": {
                "APP": {
                    "client_id": "google-client-id",
                    "secret": "google-client-secret",
                    "key": "",
                },
            },
            "telegram": {
                "APP": {
                    "client_id": "123456789",
                    "secret": "123456789:telegram-token",
                    "key": "",
                },
            },
        }
    )
    def test_configured_provider_redirects_to_allauth(self):
        response = self.client.get(
            reverse("social_login_start", args=["google"])
        )

        self.assertRedirects(
            response,
            f"{reverse('google_login')}?process=login",
            fetch_redirect_response=False,
        )
