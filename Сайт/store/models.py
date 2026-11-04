import json
import os
import urllib.parse
import urllib.request

from django.conf import settings
from django.db import models
from django.utils import timezone


class Category(models.Model):
    name = models.CharField("Nomi", max_length=80, unique=True)
    slug = models.SlugField("Slug", max_length=80, unique=True)
    order = models.PositiveSmallIntegerField("Tartib", default=0)

    class Meta:
        ordering = ("order", "name")
        verbose_name = "kategoriya"
        verbose_name_plural = "kategoriyalar"

    def __str__(self):
        return self.name


class Product(models.Model):
    VISUAL_CHOICES = [
        ("phone", "Telefon"),
        ("laptop", "Noutbuk"),
        ("tablet", "Planshet"),
        ("watch", "Soat"),
    ]

    category = models.ForeignKey(
        Category,
        verbose_name="Kategoriya",
        related_name="products",
        on_delete=models.PROTECT,
    )
    name = models.CharField("Nomi", max_length=120)
    slug = models.SlugField("Slug", max_length=120, unique=True)
    tagline = models.CharField("Qisqa tavsif", max_length=180)
    image_url = models.URLField("Mahsulot rasmi URL manzili", blank=True)
    price = models.PositiveBigIntegerField("Narxi (so'm)")
    color = models.CharField("Rang kodi", max_length=7, default="#c7c7c4")
    finish = models.CharField("Qoplama", max_length=80, blank=True)
    visual = models.CharField("Mahsulot tasviri", max_length=20, choices=VISUAL_CHOICES)
    badge = models.CharField("Belgisi", max_length=40, blank=True)
    is_featured = models.BooleanField("Bosh sahifada ko'rsatish", default=True)
    created_at = models.DateTimeField("Yaratilgan", auto_now_add=True)
    updated_at = models.DateTimeField("Yangilangan", auto_now=True)

    class Meta:
        ordering = ("-is_featured", "category__order", "name")
        verbose_name = "mahsulot"
        verbose_name_plural = "mahsulotlar"

    def __str__(self):
        return self.name

    @property
    def price_display(self):
        return f"{self.price:,}".replace(",", " ")


class Profile(models.Model):
    MAX_CODE_ATTEMPTS = 5
    REGISTRATION_SOURCE_CHOICES = [
        ("site", "Website"),
        ("bot", "Telegram bot"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Foydalanuvchi",
        related_name="profiles",
        on_delete=models.CASCADE,
    )
    avatar = models.ImageField("Profil rasmi", upload_to="avatars/", blank=True)
    first_name = models.CharField("Ism", max_length=80, blank=True)
    last_name = models.CharField("Familiya", max_length=80, blank=True)
    phone = models.CharField("Telefon raqami", max_length=20, blank=True)
    bio = models.CharField("Bio", max_length=500, blank=True)
    activation_code = models.CharField("Tasdiqlash kodi", max_length=6, blank=True)
    code_created_at = models.DateTimeField("Kod yuborilgan vaqt", null=True, blank=True)
    code_attempts = models.PositiveSmallIntegerField("Noto‘g‘ri urinishlar", default=0)
    telegram_chat_id = models.BigIntegerField("Telegram chat ID", null=True, blank=True, unique=True)
    telegram_username = models.CharField("Telegram username", max_length=80, blank=True)
    registration_source = models.CharField(
        "Ro‘yxatdan o‘tish manbai",
        max_length=20,
        choices=REGISTRATION_SOURCE_CHOICES,
        default="site",
    )

    class Meta:
        verbose_name = "profil"
        verbose_name_plural = "foydalanuvchi profillari"

    def __str__(self):
        return self.user.email or self.user.username

    def is_code_valid(self):
        if self.code_created_at is None or self.code_attempts >= self.MAX_CODE_ATTEMPTS:
            return False
        return (timezone.now() - self.code_created_at).total_seconds() < 600


def send_telegram_message(chat_id, text):
    token = os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("BOT_TOKEN")
    if not token or not chat_id:
        return None

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    data = urllib.parse.urlencode(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception:
        return None


def notify_registration_to_admin(user, source="site", telegram_data=None):
    profile = get_profile_for_user(user)
    if source == "bot":
        telegram_data = telegram_data or {}
        chat_id = telegram_data.get("chat_id")
        username = telegram_data.get("username") or ""
        if chat_id:
            profile.telegram_chat_id = int(chat_id)
        if username:
            profile.telegram_username = username
        profile.registration_source = "bot"
    else:
        profile.registration_source = "site"

    profile.first_name = profile.first_name or getattr(user, "first_name", "") or ""
    profile.last_name = profile.last_name or getattr(user, "last_name", "") or ""
    profile.save(
        update_fields=(
            "first_name",
            "last_name",
            "telegram_chat_id",
            "telegram_username",
            "registration_source",
        )
    )

    admin_chat_id = os.environ.get("ADMIN_CHAT_ID", "8803005871")
    user_name = getattr(user, "username", "") or "-"
    email = getattr(user, "email", "") or "-"
    first_name = profile.first_name or "-"
    last_name = profile.last_name or "-"
    username = profile.telegram_username or "-"
    chat_id_raw = telegram_data.get("chat_id") if telegram_data else None
    chat_id = profile.telegram_chat_id or chat_id_raw or "-"
    message = (
        "<b>Yangi foydalanuvchi ro'yxatdan o'tdi</b>\n"
        f"User: {user_name}\n"
        f"Email: {email}\n"
        f"Ism: {first_name}\n"
        f"Familiya: {last_name}\n"
        f"Manba: {source}\n"
        f"Telegram username: @{username if username != '-' else '-'}\n"
        f"Telegram chat ID: {chat_id}\n"
        f"Sana: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    return send_telegram_message(admin_chat_id, message)


def get_profile_for_user(user):
    profile = Profile.objects.filter(user=user).order_by("pk").first()
    if profile is None:
        profile = Profile.objects.create(user=user)
    return profile


class Order(models.Model):
    PAYMENT_CHOICES = [
        ("card", "Karta"),
        ("cash", "Naqd"),
        ("delivery", "Yetkazib berish"),
    ]
    STATUS_CHOICES = [
        ("pending", "Kutilmoqda"),
        ("confirmed", "Tasdiqlangan"),
        ("shipped", "Yuborildi"),
        ("completed", "Yakunlandi"),
        ("cancelled", "Bekor qilindi"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Foydalanuvchi",
        related_name="orders",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    first_name = models.CharField("Ism", max_length=80)
    last_name = models.CharField("Familiya", max_length=80, blank=True)
    email = models.EmailField("Email manzili")
    phone = models.CharField("Telefon raqami", max_length=20)
    address = models.CharField("Manzil", max_length=300, blank=True)
    payment_method = models.CharField("To‘lov usuli", max_length=20, choices=PAYMENT_CHOICES, default="card")
    total_price = models.PositiveBigIntegerField("Jami narx (so‘m)", default=0)
    status = models.CharField("Holat", max_length=20, choices=STATUS_CHOICES, default="pending")
    notes = models.CharField("Izoh", max_length=500, blank=True)
    created_at = models.DateTimeField("Yaratilgan vaqt", auto_now_add=True)
    updated_at = models.DateTimeField("Yangilangan vaqt", auto_now=True)

    class Meta:
        verbose_name = "buyurtma"
        verbose_name_plural = "buyurtmalar"
        ordering = ("-created_at",)

    def __str__(self):
        return f"Buyurtma #{self.pk} — {self.first_name} {self.last_name}".strip()

    @property
    def total_display(self):
        return f"{self.total_price:,}".replace(",", " ")


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        verbose_name="Buyurtma",
        related_name="items",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        verbose_name="Mahsulot",
        related_name="order_items",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    product_name = models.CharField("Mahsulot nomi", max_length=150)
    product_price = models.PositiveBigIntegerField("Mahsulot narxi (so‘m)")
    quantity = models.PositiveSmallIntegerField("Miqdor", default=1)

    class Meta:
        verbose_name = "buyurtma elementi"
        verbose_name_plural = "buyurtma elementlari"

    def __str__(self):
        return f"{self.product_name} x{self.quantity}"

    @property
    def subtotal(self):
        return self.product_price * self.quantity

    @property
    def subtotal_display(self):
        return f"{self.subtotal:,}".replace(",", " ")
