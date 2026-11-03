import django.core.validators
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
            name='BodyWeightEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(db_index=True, verbose_name='fecha')),
                ('weight_kg', models.DecimalField(decimal_places=2, max_digits=5, validators=[django.core.validators.MinValueValidator(20), django.core.validators.MaxValueValidator(400)], verbose_name='peso (kg)')),
                ('body_fat_pct', models.DecimalField(blank=True, decimal_places=1, max_digits=4, null=True, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(70)], verbose_name='grasa corporal (%)')),
                ('notes', models.TextField(blank=True, max_length=1000, verbose_name='notas')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='registrado')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bodyweight_entries', to=settings.AUTH_USER_MODEL, verbose_name='usuario')),
            ],
            options={
                'verbose_name': 'registro de peso',
                'verbose_name_plural': 'registros de peso',
                'ordering': ['-date'],
                'indexes': [models.Index(fields=['user', '-date'], name='bodyweight__user_id_f1ba10_idx')],
                'constraints': [models.UniqueConstraint(fields=('user', 'date'), name='unique_weight_per_day')],
            },
        ),
    ]
