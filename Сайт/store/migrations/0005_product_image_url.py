from django.db import migrations, models


PRODUCT_IMAGES = {
    "iphone-17-pro": "https://images.unsplash.com/photo-1592750475338-74b7b21085ab?auto=format&fit=crop&w=1200&q=85",
    "macbook-air": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=1200&q=85",
    "ipad-pro": "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?auto=format&fit=crop&w=1200&q=85",
    "apple-watch-ultra": "https://images.unsplash.com/photo-1434493789847-2f02dc6ca35d?auto=format&fit=crop&w=1200&q=85",
}


def add_catalog_images(apps, _schema_editor):
    Product = apps.get_model("store", "Product")
    for slug, image_url in PRODUCT_IMAGES.items():
        Product.objects.filter(slug=slug).update(image_url=image_url)


class Migration(migrations.Migration):
    dependencies = [("store", "0004_profile_code_attempts")]

    operations = [
        migrations.AddField(
            model_name="product",
            name="image_url",
            field=models.URLField(blank=True, verbose_name="Mahsulot rasmi URL manzili"),
        ),
        migrations.RunPython(add_catalog_images, migrations.RunPython.noop),
    ]