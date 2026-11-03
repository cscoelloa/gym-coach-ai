from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('aiassist', '0002_aigeneration_request_params'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProgrammingRules',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('goal', models.CharField(choices=[('hypertrophy', 'Hipertrofia'), ('strength', 'Fuerza'), ('endurance', 'Resistencia muscular')], max_length=16, unique=True, verbose_name='objetivo')),
                ('sets_min', models.PositiveSmallIntegerField(default=3, verbose_name='series mínimas por ejercicio')),
                ('sets_max', models.PositiveSmallIntegerField(default=4, verbose_name='series máximas por ejercicio')),
                ('reps_min', models.PositiveSmallIntegerField(help_text='Una banda por objetivo, no un número por ejercicio: dentro de ella caben 8-12 en un press y 12-20 en un curl, que son las dos cosas correctas.', verbose_name='repeticiones mínimas')),
                ('reps_max', models.PositiveSmallIntegerField(verbose_name='repeticiones máximas')),
                ('rest_min_compound', models.PositiveSmallIntegerField(help_text='Con menos, la serie siguiente cae por fatiga y no por estímulo.', verbose_name='descanso mínimo en compuestos (s)')),
                ('rest_min_isolation', models.PositiveSmallIntegerField(verbose_name='descanso mínimo en aislamiento (s)')),
                ('sets_min_per_muscle_day', models.PositiveSmallIntegerField(help_text='Se acota a lo que el día permite: con tres ejercicios y tres músculos no se pueden exigir seis series a cada uno.', verbose_name='series mínimas por músculo y día')),
            ],
            options={
                'verbose_name': 'reglas de programación',
                'verbose_name_plural': 'reglas de programación',
                'ordering': ['goal'],
            },
        ),
    ]
