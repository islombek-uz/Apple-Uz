from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("store", "0005_product_image_url")]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="pending_email",
            field=models.EmailField(blank=True, max_length=254, verbose_name="Tasdiqlanishi kutilayotgan email"),
        ),
    ]