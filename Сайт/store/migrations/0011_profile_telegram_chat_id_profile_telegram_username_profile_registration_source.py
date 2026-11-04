from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0010_profile_bio_profile_first_name_profile_last_name_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="telegram_chat_id",
            field=models.BigIntegerField(
                blank=True,
                null=True,
                unique=True,
                verbose_name="Telegram chat ID",
            ),
        ),
        migrations.AddField(
            model_name="profile",
            name="telegram_username",
            field=models.CharField(blank=True, max_length=80, verbose_name="Telegram username"),
        ),
        migrations.AddField(
            model_name="profile",
            name="registration_source",
            field=models.CharField(
                choices=[("site", "Website"), ("bot", "Telegram bot")],
                default="site",
                max_length=20,
                verbose_name="Ro‘yxatdan o‘tish manbai",
            ),
        ),
    ]
