from django.db import migrations, models


PRODUCT_DETAILS = {
    "iphone-17-pro": {
        "description": "Kundalik aloqa, suratga olish va mobil ijod uchun mo‘ljallangan smartfon. Pro darajadagi imkoniyatlari ish va hordiqni bitta qurilmada jamlaydi.",
        "highlights": {
            "Kamera": "Kundalik suratlar va ijodiy kontent uchun.",
            "Foydalanish": "Aloqa, ilovalar va ko‘p vazifali ishlar uchun.",
            "Dizayn": "Cho‘l titani rangidagi Pro uslub.",
        },
    },
    "macbook-air": {
        "description": "Yengil noutbuk o‘qish, ish va safarda foydalanishga mos. Hujjatlar, brauzer, videoqo‘ng‘iroqlar va kundalik ijodiy vazifalarni qulay bajarishga yordam beradi.",
        "highlights": {
            "Ish va o‘qish": "Hujjatlar, taqdimotlar va brauzer bilan ishlash uchun.",
            "Ijodiy ishlar": "Rasmlar, media va kundalik ijodiy loyihalar uchun.",
            "Dizayn": "Yengil korpus va osmonrang qoplama.",
        },
    },
    "ipad-pro": {
        "description": "Katta ekranli planshet ijod, o‘qish va ko‘ngilochar kontent uchun qulay. G‘oyalarni yozib olish, chizish va media tomosha qilishda yordam beradi.",
        "highlights": {
            "Ijod": "Chizish, qaydlar va g‘oyalarni ishlab chiqish uchun.",
            "Ko‘ngilochar kontent": "Video, kitob va ilovalarni katta ekranda ko‘rish uchun.",
            "Dizayn": "Kumushrang qoplama.",
        },
    },
    "apple-watch-ultra": {
        "description": "Faol kundalik foydalanish va sayohatlar uchun mo‘ljallangan aqlli soat. Harakat, mashg‘ulotlar va vaqt haqidagi ma’lumotlarni bilakda kuzatishga yordam beradi.",
        "highlights": {
            "Faol hayot": "Mashg‘ulotlar va kundalik harakatlarni kuzatish uchun.",
            "Safar": "Vaqt va kundalik bildirishnomalarni bilakda ko‘rish uchun.",
            "Dizayn": "Tabiiy titan rangidagi mustahkam uslub.",
        },
    },
}


def populate_product_details(apps, _schema_editor):
    Product = apps.get_model("store", "Product")
    for slug, details in PRODUCT_DETAILS.items():
        Product.objects.filter(slug=slug).update(**details)


class Migration(migrations.Migration):
    dependencies = [
        (
            "store",
            "0011_profile_telegram_chat_id_profile_telegram_username_profile_registration_source",
        )
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="description",
            field=models.TextField(blank=True, verbose_name="Batafsil tavsif"),
        ),
        migrations.AddField(
            model_name="product",
            name="highlights",
            field=models.JSONField(blank=True, default=dict, verbose_name="Muhim jihatlar"),
        ),
        migrations.RunPython(populate_product_details, migrations.RunPython.noop),
    ]