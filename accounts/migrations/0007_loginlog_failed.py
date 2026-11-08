import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0006_user_country"),
    ]

    operations = [
        migrations.AddField(
            model_name="loginlog",
            name="username_tried",
            field=models.CharField(
                blank=True, max_length=254, verbose_name="Denenen kullanici adi"
            ),
        ),
        migrations.AlterField(
            model_name="loginlog",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="login_logs",
                to=settings.AUTH_USER_MODEL,
                verbose_name="User",
            ),
        ),
        migrations.AlterField(
            model_name="loginlog",
            name="event_type",
            field=models.CharField(
                choices=[
                    ("LOGIN", "Вход"),
                    ("LOGOUT", "Выход"),
                    ("FAILED", "Неудачный вход"),
                ],
                max_length=10,
                verbose_name="Event type",
            ),
        ),
    ]
