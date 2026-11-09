from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0007_loginlog_failed"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="country",
            field=models.CharField(
                blank=True,
                help_text=(
                    "Tek ulke kisiti (eski alan, geriye uyumlu). Bos = tek-ulke "
                    "kisiti yok. is_staff ise tum ulkeler. Coklu kisit icin "
                    "allowed_countries + country_mode kullanin."
                ),
                max_length=45,
                verbose_name="Country",
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="allowed_countries",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text=(
                    "Список названий стран (как в данных, напр. "
                    "['Belarusian','Russia','Ukraine']). Работает вместе с "
                    "country_mode."
                ),
                verbose_name="Разрешённые страны (список)",
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="country_mode",
            field=models.CharField(
                choices=[
                    ("none", "Нет (один country ниже)"),
                    ("only", "Только эти страны"),
                    ("except", "Все, кроме этих стран"),
                ],
                default="none",
                help_text=(
                    "only = только allowed_countries; except = все, кроме "
                    "allowed_countries; none = использовать одно поле country."
                ),
                max_length=10,
                verbose_name="Режим стран",
            ),
        ),
    ]
