import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('notifications', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SuscripcionPush',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('endpoint', models.URLField(max_length=1000, unique=True, verbose_name='endpoint')),
                ('p256dh', models.CharField(max_length=200, verbose_name='clave p256dh')),
                ('auth', models.CharField(max_length=100, verbose_name='clave auth')),
                ('creada', models.DateTimeField(auto_now_add=True, verbose_name='creada')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='suscripciones_push', to=settings.AUTH_USER_MODEL, verbose_name='usuario')),
            ],
            options={
                'verbose_name': 'suscripción push',
                'verbose_name_plural': 'suscripciones push',
            },
        ),
    ]
