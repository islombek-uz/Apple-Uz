from django.db import migrations


def seed_catalog(apps, _schema_editor):
    Category = apps.get_model("store", "Category")
    Product = apps.get_model("store", "Product")

    categories = {
        "iphone": Category.objects.create(name="iPhone", slug="iphone", order=1),
        "mac": Category.objects.create(name="Mac", slug="mac", order=2),
        "ipad": Category.objects.create(name="iPad", slug="ipad", order=3),
        "watch": Category.objects.create(name="Watch", slug="watch", order=4),
    }
    products = [
        ("iphone", "iPhone 17 Pro", "iphone-17-pro", "Pro darajadagi quvvat. Har bir kadrda.", 14999000, "#b8a58f", "Cho'l titani", "phone", "Yangi"),
        ("mac", "MacBook Air", "macbook-air", "Yengil. Tez. Va hamisha tayyor.", 13499000, "#bcc7d0", "Osmonrang", "laptop", ""),
        ("ipad", "iPad Pro", "ipad-pro", "Tasavvuringizga joy oching.", 12999000, "#c7c7c4", "Kumushrang", "tablet", ""),
        ("watch", "Apple Watch Ultra", "apple-watch-ultra", "Sarguzashtga doim tayyor.", 10499000, "#d08b51", "Tabiiy titan", "watch", ""),
    ]
    for category, name, slug, tagline, price, color, finish, visual, badge in products:
        Product.objects.create(
            category=categories[category],
            name=name,
            slug=slug,
            tagline=tagline,
            price=price,
            color=color,
            finish=finish,
            visual=visual,
            badge=badge,
        )


def remove_catalog(apps, _schema_editor):
    Product = apps.get_model("store", "Product")
    Category = apps.get_model("store", "Category")
    Product.objects.filter(slug__in=("iphone-17-pro", "macbook-air", "ipad-pro", "apple-watch-ultra")).delete()
    Category.objects.filter(slug__in=("iphone", "mac", "ipad", "watch")).delete()


class Migration(migrations.Migration):
    dependencies = [("store", "0001_initial")]

    operations = [migrations.RunPython(seed_catalog, remove_catalog)]