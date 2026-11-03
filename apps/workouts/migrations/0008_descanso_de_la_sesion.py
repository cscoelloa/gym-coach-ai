from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('workouts', '0007_renumerar_series'),
    ]

    operations = [
        migrations.AddField(
            model_name='workoutsession',
            name='rest_ends_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='fin del descanso'),
        ),
        migrations.AddField(
            model_name='workoutsession',
            name='rest_seconds',
            field=models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='descanso total (s)'),
        ),
    ]
