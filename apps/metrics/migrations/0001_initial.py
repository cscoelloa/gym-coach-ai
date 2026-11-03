import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Metric',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.SlugField(max_length=64, unique=True, verbose_name='clave')),
                ('label', models.CharField(max_length=120, verbose_name='nombre')),
                ('description', models.TextField(verbose_name='descripción')),
                ('unit', models.CharField(blank=True, max_length=32, verbose_name='unidad')),
                ('category', models.CharField(db_index=True, max_length=32, verbose_name='categoría')),
                ('chart', models.CharField(max_length=16, verbose_name='tipo de gráfico')),
                ('order', models.PositiveSmallIntegerField(default=0, verbose_name='orden')),
                ('is_active', models.BooleanField(default=True, help_text='Desactivada, deja de calcularse y desaparece del catálogo de los usuarios.', verbose_name='activa')),
                ('send_to_ai', models.BooleanField(default=True, help_text='Si se incluye en el prompt del análisis de progreso.', verbose_name='enviar a la IA')),
                ('default_visible', models.BooleanField(default=True, help_text='Si aparece en el panel de quien no haya elegido nada todavía.', verbose_name='visible por defecto')),
            ],
            options={
                'verbose_name': 'métrica',
                'verbose_name_plural': 'métricas',
                'ordering': ['category', 'order'],
            },
        ),
        migrations.CreateModel(
            name='UserMetricPreference',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_visible', models.BooleanField(default=True, verbose_name='visible')),
                ('order', models.PositiveSmallIntegerField(default=0, verbose_name='orden')),
                ('metric', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='preferences', to='metrics.metric', verbose_name='métrica')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='metric_preferences', to=settings.AUTH_USER_MODEL, verbose_name='usuario')),
            ],
            options={
                'verbose_name': 'preferencia de métrica',
                'verbose_name_plural': 'preferencias de métricas',
                'ordering': ['order'],
                'constraints': [models.UniqueConstraint(fields=('user', 'metric'), name='unique_metric_per_user')],
            },
        ),
    ]
