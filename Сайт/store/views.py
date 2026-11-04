import json
import secrets

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import (
    CheckoutForm,
    EmailChangeForm,
    LoginForm,
    PasswordResetCodeForm,
    PasswordResetRequestForm,
    ProfileAvatarForm,
    RegisterForm,
    VerificationCodeForm,
    VerificationResendForm,
)
from .models import (
    Category,
    Order,
    OrderItem,
    Product,
    get_profile_for_user,
    notify_registration_to_admin,
)

User = get_user_model()


def _send_code_to_email(user, recipient, subject, purpose):
    profile = get_profile_for_user(user)
    activation_code = str(secrets.randbelow(900000) + 100000)
    send_mail(
        subject=subject,
        message=(
            f"Salom {user.username}!\n\n"
            f"{purpose} uchun kodingiz: {activation_code}\n"
            "Kod 10 daqiqa davomida amal qiladi."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[recipient],
        fail_silently=False,
    )
    profile.activation_code = activation_code
    profile.code_created_at = timezone.now()
    profile.code_attempts = 0
    profile.save(
        update_fields=("activation_code", "code_created_at", "code_attempts")
    )


def _send_verification_code(user):
    _send_code_to_email(
        user,
        user.email,
        "Apple Store hisobini tasdiqlash",
        "Hisobni tasdiqlash",
    )


def home(request):
    selected_category = request.GET.get("category", "")
    search_query = request.GET.get("q", "").strip()
    products = Product.objects.select_related("category")
    if selected_category:
        products = products.filter(category__slug=selected_category)
    if search_query:
        products = products.filter(name__icontains=search_query)
    products = list(products)
    hero_product = next(
        (product for product in products if product.slug == "iphone-17-pro"),
        products[0] if products else None,
    )
    return render(
        request,
        "store/storefront.html",
        {
            "products": products,
            "categories": Category.objects.all(),
            "selected_category": selected_category,
            "search_query": search_query,
            "hero_product": hero_product,
        },
    )


def github_guide(request):
    return render(request, "store/github_guide.html")


@login_required(login_url="login")
def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related("category"), slug=slug
    )
    return render(request, "store/product_detail.html", {"product": product})


def register_page(request):
    if request.user.is_authenticated:
        return redirect("home")

    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        notify_registration_to_admin(user, source="site")
        try:
            _send_verification_code(user)
        except Exception:
            user.delete()
            messages.error(
                request,
                "Tasdiqlash xatini yuborib bo‘lmadi. Email sozlamalarini tekshirib, qayta urinib ko‘ring.",
            )
        else:
            request.session["verify_email"] = user.email
            messages.info(request, "Email manzilingizga tasdiqlash kodi yuborildi.")
            return redirect("verify_code")

    return render(request, "store/register.html", {"form": form})


def verify_code_page(request):
    email = request.session.get("verify_email")
    if not email:
        return redirect("register")

    user = User.objects.filter(email__iexact=email, is_active=False).first()
    if user is None:
        request.session.pop("verify_email", None)
        return redirect("register")

    profile = get_profile_for_user(user)
    form = VerificationCodeForm(request.POST or None)

    if request.method == "POST" and request.POST.get("action") == "resend":
        try:
            _send_verification_code(user)
        except Exception:
            messages.error(request, "Yangi kod yuborilmadi. Email sozlamalarini tekshiring.")
        else:
            messages.success(request, "Yangi tasdiqlash kodi yuborildi.")
        form = VerificationCodeForm()
    elif request.method == "POST" and form.is_valid():
        if profile.code_attempts >= profile.MAX_CODE_ATTEMPTS:
            messages.error(request, "Urinishlar limiti tugadi. Yangi kod yuboring.")
        elif not profile.is_code_valid():
            messages.error(request, "Kod muddati tugagan. Yangi kod yuboring.")
        elif secrets.compare_digest(profile.activation_code, form.cleaned_data["code"]):
            user.is_active = True
            user.save(update_fields=("is_active",))
            profile.activation_code = ""
            profile.code_created_at = None
            profile.code_attempts = 0
            profile.save(
                update_fields=("activation_code", "code_created_at", "code_attempts")
            )
            request.session.pop("verify_email", None)
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            messages.success(request, "Hisobingiz faollashtirildi. Xush kelibsiz!")
            return redirect("home")
        else:
            profile.code_attempts += 1
            profile.save(update_fields=("code_attempts",))
            if profile.code_attempts >= profile.MAX_CODE_ATTEMPTS:
                messages.error(request, "Urinishlar limiti tugadi. Yangi kod yuboring.")
            else:
                messages.error(request, "Tasdiqlash kodi noto‘g‘ri.")

    return render(
        request,
        "store/verify_code.html",
        {"form": form, "email": email},
    )


def resend_verification_page(request):
    form = VerificationResendForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"].strip()
        user = User.objects.filter(email__iexact=email, is_active=False).first()
        if user is not None:
            try:
                _send_verification_code(user)
            except Exception:
                messages.error(
                    request,
                    "Kod yuborilmadi. Email server sozlamalarini tekshiring.",
                )
            else:
                request.session["verify_email"] = user.email
                messages.success(request, "Yangi tasdiqlash kodi yuborildi.")
                return redirect("verify_code")
        else:
            messages.info(
                request,
                "Agar hisob tasdiqlanmagan bo‘lsa, yangi kod yuboriladi.",
            )
    return render(
        request,
        "store/resend_verification.html",
        {
            "form": form,
            "email_uses_console": (
                settings.EMAIL_BACKEND
                == "django.core.mail.backends.console.EmailBackend"
            ),
        },
    )


@login_required(login_url="login")
def change_email_page(request):
    form = EmailChangeForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        new_email = form.cleaned_data["email"]
        try:
            _send_code_to_email(
                request.user,
                new_email,
                "Apple Store email manzilini tasdiqlash",
                "Yangi email manzilini tasdiqlash",
            )
        except Exception:
            messages.error(request, "Tasdiqlash kodi yuborilmadi. Email sozlamalarini tekshiring.")
        else:
            request.session["pending_email"] = new_email
            request.session["email_change_user_id"] = request.user.pk
            messages.info(request, "Yangi email manzilingizga tasdiqlash kodi yuborildi.")
            return redirect("verify_email_change")

    return render(request, "store/change_email.html", {"form": form})


@login_required(login_url="login")
def verify_email_change_page(request):
    pending_email = request.session.get("pending_email")
    if (
        not pending_email
        or request.session.get("email_change_user_id") != request.user.pk
    ):
        request.session.pop("pending_email", None)
        request.session.pop("email_change_user_id", None)
        return redirect("change_email")

    profile = get_profile_for_user(request.user)
    form = VerificationCodeForm(request.POST or None)

    if request.method == "POST" and request.POST.get("action") == "resend":
        try:
            _send_code_to_email(
                request.user,
                pending_email,
                "Apple Store email manzilini tasdiqlash",
                "Yangi email manzilini tasdiqlash",
            )
        except Exception:
            messages.error(request, "Yangi kod yuborilmadi. Email sozlamalarini tekshiring.")
        else:
            messages.success(request, "Yangi tasdiqlash kodi yuborildi.")
        form = VerificationCodeForm()
    elif request.method == "POST" and form.is_valid():
        if profile.code_attempts >= profile.MAX_CODE_ATTEMPTS:
            messages.error(request, "Urinishlar limiti tugadi. Yangi kod yuboring.")
        elif not profile.is_code_valid():
            messages.error(request, "Kod muddati tugagan. Yangi kod yuboring.")
        elif secrets.compare_digest(profile.activation_code, form.cleaned_data["code"]):
            if User.objects.filter(email__iexact=pending_email).exclude(
                pk=request.user.pk
            ).exists():
                messages.error(request, "Bu email manzili boshqa hisobda ishlatilmoqda.")
                return redirect("change_email")
            request.user.email = pending_email
            request.user.save(update_fields=("email",))
            profile.activation_code = ""
            profile.code_created_at = None
            profile.code_attempts = 0
            profile.save(
                update_fields=("activation_code", "code_created_at", "code_attempts")
            )
            request.session.pop("pending_email", None)
            request.session.pop("email_change_user_id", None)
            messages.success(request, "Email manzilingiz muvaffaqiyatli yangilandi.")
            return redirect("profile")
        else:
            profile.code_attempts += 1
            profile.save(update_fields=("code_attempts",))
            messages.error(request, "Tasdiqlash kodi noto‘g‘ri.")

    return render(
        request,
        "store/verify_code.html",
        {"form": form, "email": pending_email, "email_change": True},
    )


def password_reset_request_page(request):
    if request.method == "POST":
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"].strip()
            request.session["password_reset_email"] = email
            user = User.objects.filter(email__iexact=email, is_active=True).first()
            if user is not None:
                try:
                    _send_code_to_email(
                        user,
                        user.email,
                        "Apple Store parolni tiklash",
                        "Parolni tiklash",
                    )
                except Exception:
                    pass
            messages.info(
                request,
                "Agar bu email hisobga bog‘langan bo‘lsa, tasdiqlash kodi yuboriladi.",
            )
            return redirect("password_reset_verify")
    else:
        form = PasswordResetRequestForm()
    return render(
        request,
        "store/password_reset_request.html",
        {
            "form": form,
            "email_uses_console": (
                settings.EMAIL_BACKEND
                == "django.core.mail.backends.console.EmailBackend"
            ),
        },
    )


def password_reset_verify_page(request):
    email = request.session.get("password_reset_email")
    if not email:
        return redirect("password_reset_request")

    user = User.objects.filter(email__iexact=email, is_active=True).first()
    profile = get_profile_for_user(user) if user is not None else None
    form = PasswordResetCodeForm(request.POST or None, user=user)

    if request.method == "POST" and request.POST.get("action") == "resend":
        if user is not None:
            try:
                _send_code_to_email(
                    user,
                    user.email,
                    "Apple Store parolni tiklash",
                    "Parolni tiklash",
                )
            except Exception:
                pass
        messages.info(
            request,
            "Agar bu email hisobga bog‘langan bo‘lsa, yangi kod yuboriladi.",
        )
        form = PasswordResetCodeForm(user=user)
    elif request.method == "POST" and form.is_valid():
        if (
            user is None
            or
            profile is None
            or profile.code_attempts >= profile.MAX_CODE_ATTEMPTS
            or not profile.is_code_valid()
            or not secrets.compare_digest(
                profile.activation_code, form.cleaned_data["code"]
            )
        ):
            if profile is not None and profile.code_attempts < profile.MAX_CODE_ATTEMPTS:
                profile.code_attempts += 1
                profile.save(update_fields=("code_attempts",))
            messages.error(request, "Tasdiqlash kodi noto‘g‘ri yoki muddati tugagan.")
        else:
            user.set_password(form.cleaned_data["new_password1"])
            user.save(update_fields=("password",))
            profile.activation_code = ""
            profile.code_created_at = None
            profile.code_attempts = 0
            profile.save(
                update_fields=("activation_code", "code_created_at", "code_attempts")
            )
            request.session.pop("password_reset_email", None)
            messages.success(request, "Parolingiz yangilandi. Yangi parol bilan kiring.")
            return redirect("login")

    return render(
        request,
        "store/password_reset_verify.html",
        {"form": form, "email": email},
    )


@login_required(login_url="login")
def profile_page(request):
    profile = get_profile_for_user(request.user)
    if request.method == "POST":
        form = ProfileAvatarForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil ma’lumotlari saqlandi.")
            return redirect("profile")
    else:
        form = ProfileAvatarForm(instance=profile)

    return render(
        request,
        "store/profile.html",
        {"form": form, "profile": profile},
    )


def login_page(request):
    if request.user.is_authenticated:
        return redirect("home")

    form = LoginForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        messages.success(request, "Hisobingizga muvaffaqiyatli kirdingiz.")
        return redirect("home")
    return render(request, "store/login.html", {"form": form})


def social_login_start(request, provider):
    providers = {
        "google": ("Google", "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET"),
        "telegram": ("Telegram", "TELEGRAM_BOT_ID", "TELEGRAM_BOT_TOKEN"),
    }
    if provider not in providers:
        return redirect("login")

    provider_name, client_id_env, secret_env = providers[provider]
    app = settings.SOCIALACCOUNT_PROVIDERS[provider]["APP"]
    if not app["client_id"] or not app["secret"]:
        return render(
            request,
            "store/social_setup_required.html",
            {
                "provider_name": provider_name,
                "client_id_env": client_id_env,
                "secret_env": secret_env,
                "callback_url": request.build_absolute_uri(
                    reverse(f"{provider}_callback")
                ),
            },
        )

    return redirect(f"{reverse(f'{provider}_login')}?process=login")


def cart_page(request):
    initial = {}
    if request.user.is_authenticated:
        profile = get_profile_for_user(request.user)
        initial = {
            "first_name": profile.first_name or request.user.first_name,
            "last_name": profile.last_name or request.user.last_name,
            "email": request.user.email,
            "phone": profile.phone,
        }
    form = CheckoutForm(initial=initial)
    clear_cart = request.session.pop("clear_cart_after_order", False)
    return render(
        request,
        "store/cart.html",
        {
            "form": form,
            "clear_cart": clear_cart,
            "cart_catalog": list(
                Product.objects.values("id", "name", "price")
            ),
        },
    )


def checkout_page(request):
    if request.method != "POST":
        return redirect("cart")

    form = CheckoutForm(request.POST)
    raw_items = request.POST.get("cart_items", "")
    try:
        submitted_items = json.loads(raw_items)
    except (TypeError, ValueError):
        submitted_items = None

    quantities = {}
    valid_items = False
    if isinstance(submitted_items, list) and 0 < len(submitted_items) <= 50:
        valid_items = True
        for item in submitted_items:
            if not isinstance(item, dict):
                valid_items = False
                break
            product_id = item.get("id")
            quantity = item.get("quantity")
            if (
                not isinstance(product_id, int)
                or isinstance(product_id, bool)
                or not isinstance(quantity, int)
                or isinstance(quantity, bool)
                or not 1 <= quantity <= 99
            ):
                valid_items = False
                break
            quantities[product_id] = quantities.get(product_id, 0) + quantity
            if quantities[product_id] > 99:
                valid_items = False
                break

    products = list(Product.objects.filter(pk__in=quantities)) if valid_items else []
    if not valid_items or len(products) != len(quantities) or not form.is_valid():
        if not valid_items or len(products) != len(quantities):
            messages.error(request, "Savat ma’lumotlari noto‘g‘ri yoki mahsulot endi mavjud emas.")
        return render(
            request,
            "store/cart.html",
            {
                "form": form,
                "clear_cart": False,
                "cart_catalog": list(
                    Product.objects.values("id", "name", "price")
                ),
            },
            status=400,
        )

    products_by_id = {product.pk: product for product in products}
    total_price = sum(
        products_by_id[product_id].price * quantity
        for product_id, quantity in quantities.items()
    )
    order_data = form.cleaned_data
    with transaction.atomic():
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            first_name=order_data["first_name"],
            last_name=order_data["last_name"],
            email=order_data["email"],
            phone=order_data["phone"],
            address=order_data["address"],
            payment_method=order_data["payment_method"],
            total_price=total_price,
            notes=order_data["notes"],
        )
        OrderItem.objects.bulk_create(
            [
                OrderItem(
                    order=order,
                    product=products_by_id[product_id],
                    product_name=products_by_id[product_id].name,
                    product_price=products_by_id[product_id].price,
                    quantity=quantity,
                )
                for product_id, quantity in quantities.items()
            ]
        )

    request.session["clear_cart_after_order"] = True
    messages.success(request, f"Buyurtma #{order.pk} saqlandi. To‘lov demo rejimida simulyatsiya qilindi.")
    return redirect("cart")

def logout_page(request):
    logout(request)
    messages.info(request, "Hisobingizdan chiqdingiz.")
    return redirect("home")
