# Apple Storefront

Django’da yaratilgan, Uzbek tilidagi Apple uslubidagi mahsulot vitrinası. Bosh sahifa, mahsulot tafsilotlari va brauzerda saqlanadigan demo savat mavjud. Checkout buyurtmalarni bazaga yozadi; to‘lov demo rejimida simulyatsiya qilinadi va haqiqiy pul yechilmaydi. Buyurtmalarni admin paneldan boshqaring.

## Ishga tushirish

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
py manage.py migrate
py manage.py createsuperuser
py manage.py runserver
```

Saytni `http://127.0.0.1:8000/` manzilida, Jazzmin admin panelini `http://127.0.0.1:8000/admin/` manzilida oching. Kategoriyalar va mahsulotlarni admin paneldan boshqaring; boshlang'ich demo mahsulotlar migration orqali yaratiladi. Savat localStorage’dan foydalanadi.

Ro‘yxatdan o‘tishda va profil emailini almashtirishda 6 xonali kod yuboriladi. SMTP sozlamalari bo‘lmasa, lokal ishlashda kod Django server terminalida ko‘rinadi. Haqiqiy email yuborish uchun `.env` fayliga pochta provayderingiz sozlamalarini kiriting:

```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-address@gmail.com
EMAIL_HOST_PASSWORD=your-provider-app-password
DEFAULT_FROM_EMAIL=Apple Store <your-address@gmail.com>
```

`EMAIL_HOST` va `EMAIL_HOST_USER` qiymatlarini provayderingizga moslang. Gmail uchun oddiy hisob paroli emas, App Password ishlating. `EMAIL_HOST_USER` va `EMAIL_HOST_PASSWORD` bo‘lsa, SMTP avtomatik yoqiladi; `EMAIL_BACKEND`ni qo‘lda belgilash shart emas. Kod 10 daqiqa amal qiladi va 5 ta noto‘g‘ri urinishdan so‘ng qayta yuborilishi kerak.

Parol esdan chiqsa, `/login/` sahifasidagi “Parolni unutdingizmi?” havolasini oching. Hisob emailiga yuborilgan 6 xonali kodni kiriting va yangi parol yarating. Email manzili profil ichida ham faqat yangi manzilga yuborilgan kod tasdiqlangandan keyin almashtiriladi.

## Google va Telegram orqali kirish

Ijtimoiy login tugmalari login va ro‘yxatdan o‘tish sahifalarida doim ko‘rinadi. Loyiha ishga tushganda root papkadagi `.env` faylni o‘qiydi; qiymatlarni source code’ga yozmang. `.env` Git’ga qo‘shilmaydi.

- Google Cloud Console’da loyiha tanlang/yarating, OAuth consent screen’ni sozlang (Testing rejimida ishlaydigan Google hisobini Test users ro‘yxatiga qo‘shing), so‘ng Credentials → Create credentials → OAuth client ID → Web application yarating. Authorized redirect URI sifatida `http://127.0.0.1:8000/accounts/google/login/callback/` qo‘shing. Client ID va Secret’ni root `.env` faylidagi `GOOGLE_CLIENT_ID` hamda `GOOGLE_CLIENT_SECRET` qiymatlariga yozing; secret’ni chatga yoki source code’ga qo‘tmang. Serverni qayta ishga tushiring. Sayt `localhost:8000` manzilida ochilsa, Google Console’ga `http://localhost:8000/accounts/google/login/callback/` URI’sini ham qo‘shing.
- Telegram’da BotFather orqali o‘zingizning botingizni yarating. Tokenni root `.env` faylidagi `TELEGRAM_BOT_TOKEN` ga, tokenning `:` dan oldingi raqamli qismini `TELEGRAM_BOT_ID` ga yozing. BotFather’da `/setdomain` buyrug‘i orqali bot uchun sayt domenini ro‘yxatdan o‘tkazing. Telegram OAuth `127.0.0.1` kabi lokal IP’ni qabul qilmaydi; lokal sinov uchun HTTPS tunnel (masalan, Cloudflare Tunnel yoki ngrok) ochib, tunnel hostini `ALLOWED_HOSTS`ga va BotFather domeniga qo‘shing, keyin callback’ni tunnel orqali sinang. Bot tokeni oshkor bo‘lgan bo‘lsa, BotFather’dan yangisini yarating va `.env`ni yangilang.
- Serverni qayta ishga tushiring va `/login/` sahifasidan sinang. Ishlab chiqarishda Google redirect URI hamda Telegram domenini haqiqiy HTTPS domeningizga moslang.

`.env` faylida credential’lar bo‘sh qolsa, login tugmasi sozlash bo‘yicha ko‘rsatmani ochadi.

Allauth migration’lari ham odatdagi `py manage.py migrate` buyrug‘i bilan qo‘llanadi.
