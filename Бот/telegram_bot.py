import html
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SITE_DIR = PROJECT_ROOT / "Сайт"


def load_env_file():
    for candidate in [PROJECT_ROOT / ".env", SITE_DIR / ".env"]:
        if not candidate.exists():
            continue
        for line in candidate.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if value and not os.environ.get(key):
                os.environ[key] = value


load_env_file()

BOT_TOKEN = os.environ.get("BOT_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN", "")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID", "8803005871")
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}" if BOT_TOKEN else ""
CATALOG_PAGE_SIZE = 5
CATALOG_STATE = {}


def setup_django():
    if str(SITE_DIR) not in sys.path:
        sys.path.insert(0, str(SITE_DIR))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django

    django.setup()


setup_django()


def profile_has_telegram_fields():
    try:
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute("PRAGMA table_info(store_profile)")
            columns = [row[1] for row in cursor.fetchall()]
            required = {"telegram_chat_id", "telegram_username", "registration_source"}
            return required.issubset(columns)
    except Exception:
        return False


def api_request(method, payload=None):
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set. Add TELEGRAM_BOT_TOKEN or BOT_TOKEN in .env")

    url = f"{BASE_URL}/{method}"
    data = None
    headers = {}

    if payload is not None:
        payload = payload.copy()
        if isinstance(payload.get("reply_markup"), dict):
            payload["reply_markup"] = json.dumps(payload["reply_markup"], ensure_ascii=False)
        data = urllib.parse.urlencode(payload).encode("utf-8")
        headers["Content-Type"] = "application/x-www-form-urlencoded"

    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=40) as response:
        return json.loads(response.read().decode("utf-8"))


def send_message(chat_id, text, reply_markup=None):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    if reply_markup is not None:
        payload["reply_markup"] = reply_markup
    return api_request("sendMessage", payload)


def get_updates(offset=None):
    payload = {"timeout": 30}
    if offset is not None:
        payload["offset"] = offset
    return api_request("getUpdates", payload)



def catalog_page(chat_id, query="", page=0, intro=None):
    from django.db.models import Q
    from store.models import Product

    products_query = Product.objects.select_related("category").order_by("-is_featured", "name")
    if query:
        products_query = products_query.filter(
            Q(name__icontains=query)
            | Q(category__name__icontains=query)
            | Q(tagline__icontains=query)
        )

    total = products_query.count()
    total_pages = max(1, (total + CATALOG_PAGE_SIZE - 1) // CATALOG_PAGE_SIZE)
    page = max(0, min(page, total_pages - 1))
    products = list(
        products_query[page * CATALOG_PAGE_SIZE : (page + 1) * CATALOG_PAGE_SIZE]
    )
    CATALOG_STATE[chat_id] = (query, page)
    if len(CATALOG_STATE) > 1000:
        CATALOG_STATE.pop(next(iter(CATALOG_STATE)))

    if not products:
        empty_text = "Hozircha do'konda mahsulotlar yo'q." if not query else "Bu so'rov bo'yicha mahsulot topilmadi."
        return f"{intro or ''}{empty_text}\n/catalog — katalogni ochish".strip(), None

    title = "🛍️ <b>Do'kon katalogi</b>"
    if query:
        title += f"\nQidiruv: <b>{html.escape(query)}</b>"
    title += f"\nSahifa {page + 1}/{total_pages}. Mahsulotni tanlang:"
    if intro:
        title = f"{html.escape(intro)}\n\n{title}"

    keyboard = [
        [{
            "text": f"{product.name[:30]} · {product.price_display} so'm",
            "callback_data": f"product:{product.pk}",
        }]
        for product in products
    ]
    navigation = []
    if page > 0:
        navigation.append({"text": "⬅️ Oldingi", "callback_data": f"page:{page - 1}"})
    if page + 1 < total_pages:
        navigation.append({"text": "Keyingi ➡️", "callback_data": f"page:{page + 1}"})
    if navigation:
        keyboard.append(navigation)
    if query:
        keyboard.append([{"text": "Barcha mahsulotlar", "callback_data": "catalog"}])

    return title, {"inline_keyboard": keyboard}


def product_detail(product_id):
    from store.models import Product

    try:
        product = Product.objects.select_related("category").get(pk=product_id)
    except Product.DoesNotExist:
        return "Bu mahsulot endi mavjud emas. /catalog orqali katalogni yangilang."

    visual_labels = dict(Product.VISUAL_CHOICES)
    site_url = html.escape(os.environ.get("SITE_URL", "http://127.0.0.1:8000").rstrip("/"), quote=True)
    details = [
        f"<b>{html.escape(product.name)}</b>",
        html.escape(product.tagline),
        f"\n📦 Kategoriya: {html.escape(product.category.name)}",
        f"💵 Narx: {product.price_display} so'm",
        f"🎨 Rang: {html.escape(product.color)}",
        f"Qoplama: {html.escape(product.finish or 'Ko‘rsatilmagan')}",
        f"Turi: {html.escape(visual_labels.get(product.visual, product.visual))}",
        f"Belgi: {html.escape(product.badge or 'Yo‘q')}",
        f"Tanlangan mahsulot: {'Ha' if product.is_featured else 'Yo‘q'}",
    ]
    if product.image_url:
        image_url = html.escape(product.image_url, quote=True)
        details.append(f'🖼️ <a href="{image_url}">Mahsulot rasmini ochish</a>')
    details.append(
        f'🔗 <a href="{site_url}/product/{html.escape(product.slug, quote=True)}/">Saytdagi mahsulot sahifasi</a>'
    )
    return "\n".join(details)


def handle_callback_query(callback_query):
    callback_id = callback_query.get("id")
    message = callback_query.get("message") or {}
    chat_id = (message.get("chat") or {}).get("id")
    message_id = message.get("message_id")
    data = callback_query.get("data", "")
    if callback_id:
        api_request("answerCallbackQuery", {"callback_query_id": callback_id})
    if chat_id is None or message_id is None:
        return

    query, current_page = CATALOG_STATE.get(chat_id, ("", 0))
    if data == "catalog":
        query, current_page = "", 0
        text, keyboard = catalog_page(chat_id, query, current_page)
    elif data.startswith("page:"):
        try:
            current_page = int(data.split(":", 1)[1])
        except ValueError:
            current_page = 0
        text, keyboard = catalog_page(chat_id, query, current_page)
    elif data.startswith("product:"):
        product_id = data.split(":", 1)[1]
        text = product_detail(product_id)
        keyboard = {"inline_keyboard": [[{"text": "⬅️ Natijalarga qaytish", "callback_data": f"page:{current_page}"}]]}
    else:
        return

    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    if keyboard is not None:
        payload["reply_markup"] = keyboard
    api_request("editMessageText", payload)


def create_user_from_telegram(chat_id, username, first_name, email=None):
    from django.contrib.auth import get_user_model
    from store.models import Profile, notify_registration_to_admin

    if not profile_has_telegram_fields():
        return None, "База ещё не обновлена. Сначала запустите миграцию в проекте: py manage.py migrate"

    User = get_user_model()
    if email is not None:
        email = email.strip()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            return None, "Email manzili noto'g'ri formatda. Haqiqiy email manzilingizni kiriting."
        email_domain = email.rsplit("@", 1)[1].lower()
        if email_domain in {"example.com", "example.org", "example.net"}:
            return None, "Bu faqat namuna email. Iltimos, o'zingizning haqiqiy email manzilingizni kiriting."
        if User.objects.filter(email__iexact=email).exists():
            existing = User.objects.filter(email__iexact=email).first()
            profile = Profile.objects.filter(user=existing).first()
            if profile is not None and profile.telegram_chat_id == int(chat_id):
                return existing, "Siz allaqachon ro'yxatdan o'tgansiz."
            return None, "Bu email manzili allaqachon ro'yxatdan o'tgan."

    existing_profile = Profile.objects.filter(telegram_chat_id=int(chat_id)).first()
    if existing_profile is not None:
        return existing_profile.user, "Siz allaqachon ro'yxatdan o'tgansiz."

    normalized = (username or first_name or f"user{chat_id}").strip()
    normalized = re.sub(r"[^a-zA-Z0-9_]+", "", normalized)[:30] or f"user{chat_id}"
    base_username = normalized.lower()

    username_value = base_username
    counter = 1
    while User.objects.filter(username=username_value).exists():
        username_value = f"{base_username}{counter}"
        counter += 1

    safe_email = email or f"{username_value}@telegram.local"
    user, created = User.objects.get_or_create(
        username=username_value,
        defaults={"email": safe_email, "first_name": first_name or "", "is_active": True},
    )

    if email and user.email != email:
        user.email = email
        user.first_name = user.first_name or (first_name or "")
        user.save(update_fields=("email", "first_name"))

    profile = Profile.objects.filter(user=user).first()
    if profile is None:
        profile = Profile.objects.create(user=user)

    profile.telegram_chat_id = int(chat_id)
    profile.telegram_username = username or ""
    profile.registration_source = "bot"
    profile.first_name = profile.first_name or (first_name or "")
    profile.save(update_fields=("telegram_chat_id", "telegram_username", "registration_source", "first_name"))

    if created:
        notify_registration_to_admin(user, source="bot", telegram_data={"chat_id": chat_id, "username": username})

    return user, "ok"


def handle_message(message):
    chat = message.get("chat", {})
    chat_id = chat.get("id")
    text = (message.get("text") or "").strip()

    if chat_id is None:
        return

    if not text:
        return

    if not profile_has_telegram_fields():
        send_message(
            chat_id,
            "База данных ещё не обновлена. Сначала выполните миграцию в проекте сайта:\n\npy manage.py migrate\n\nПосле этого перезапустите бота.",
        )
        return

    lower = text.lower()
    reply_markup = None
    if lower in {"/start", "/start@my_store_bot"}:
        from store.models import Profile

        profile = Profile.objects.filter(telegram_chat_id=chat_id).first()
        if profile is not None:
            response, reply_markup = catalog_page(
                chat_id,
                intro="Xush kelibsiz! Siz ro'yxatdan o'tgansiz.",
            )
        else:
            response = (
                "Xush kelibsiz, Apple Store botiga!\n\n"
                "Ro'yxatdan o'tish uchun quyidagi formatda yozing:\n"
                "Ism|haqiqiy email manzilingiz\n\n"
                "Namuna email manzillar ro'yxatdan o'tkazilmaydi."
            )
    elif lower in {"/help", "/help@my_store_bot"}:
        response = (
            "Quyidagi buyruqlardan foydalaning:\n"
            "/catalog — mahsulotlarni ko'rish\n"
            "/site — saytga o'tish\n"
            "yoki mahsulot nomini yozing, masalan: iPhone"
        )
    elif lower in {"/catalog", "/catalog@my_store_bot"}:
        response, reply_markup = catalog_page(chat_id)
    elif lower in {"/site", "/site@my_store_bot"}:
        response = f"🌐 Do'kon sayti: {html.escape(os.environ.get('SITE_URL', 'http://127.0.0.1:8000'))}"
    else:
        if "|" in text:
            parts = [item.strip() for item in text.split("|", 1)]
            if len(parts) == 2 and parts[0] and parts[1]:
                first_name, email = parts
                user, status = create_user_from_telegram(
                    chat_id,
                    chat.get("username") or first_name,
                    first_name,
                    email,
                )
                if status != "ok":
                    send_message(chat_id, status)
                    return
                if user is None:
                    send_message(chat_id, "Ro'yxatdan o'tishda xatolik yuz berdi. Qaytadan urinib ko'ring.")
                    return
                response, reply_markup = catalog_page(
                    chat_id,
                    intro=f"Tabriklamiz, {user.first_name or first_name}! Ro'yxatdan o'tdingiz.",
                )
                send_message(chat_id, response, reply_markup)
                return

        response, reply_markup = catalog_page(chat_id, query=text)

    send_message(chat_id, response, reply_markup)


def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set. Add TELEGRAM_BOT_TOKEN or BOT_TOKEN in .env")

    print("Bot started. Waiting for new Telegram messages...")
    last_update_id = None

    while True:
        try:
            result = get_updates(last_update_id)
            updates = result.get("result", [])

            for update in updates:
                update_id = update.get("update_id")
                try:
                    callback_query = update.get("callback_query")
                    if callback_query is not None:
                        handle_callback_query(callback_query)
                    else:
                        message = update.get("message")
                        if message is not None:
                            handle_message(message)
                except Exception as exc:
                    print(f"Update {update_id} failed: {exc}")
                finally:
                    if update_id is not None:
                        last_update_id = update_id + 1

        except Exception as exc:
            print(f"Error: {exc}")
            time.sleep(5)


if __name__ == "__main__":
    main()
