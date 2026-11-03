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
            name='MuscleGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.SlugField(max_length=64, unique=True, verbose_name='identificador')),
                ('name', models.CharField(max_length=64, verbose_name='nombre')),
            ],
            options={
                'verbose_name': 'grupo muscular',
                'verbose_name_plural': 'grupos musculares',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Exercise',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('external_id', models.CharField(blank=True, db_index=True, help_text='Id en el dataset original. Vacío en los ejercicios creados por usuarios.', max_length=16, null=True, unique=True, verbose_name='id del catálogo')),
                ('name', models.CharField(max_length=200, verbose_name='nombre')),
                ('slug', models.SlugField(max_length=220, unique=True, verbose_name='identificador')),
                ('category', models.CharField(blank=True, max_length=32, verbose_name='categoría')),
                ('body_part', models.CharField(choices=[('back', 'Espalda'), ('cardio', 'Cardio'), ('chest', 'Pecho'), ('lower arms', 'Antebrazos'), ('lower legs', 'Pierna inferior'), ('neck', 'Cuello'), ('shoulders', 'Hombros'), ('upper arms', 'Brazos'), ('upper legs', 'Piernas'), ('waist', 'Zona media')], db_index=True, max_length=32, verbose_name='zona')),
                ('equipment', models.CharField(blank=True, choices=[('assisted', 'Asistido'), ('band', 'Banda'), ('barbell', 'Barra'), ('body weight', 'Peso corporal'), ('bosu ball', 'Bosu'), ('cable', 'Polea'), ('dumbbell', 'Mancuerna'), ('elliptical machine', 'Elíptica'), ('ez barbell', 'Barra Z'), ('hammer', 'Máquina Hammer'), ('kettlebell', 'Kettlebell'), ('leverage machine', 'Máquina de palanca'), ('medicine ball', 'Balón medicinal'), ('olympic barbell', 'Barra olímpica'), ('resistance band', 'Banda de resistencia'), ('roller', 'Rodillo'), ('rope', 'Cuerda'), ('skierg machine', 'SkiErg'), ('sled machine', 'Trineo'), ('smith machine', 'Multipower'), ('stability ball', 'Fitball'), ('stationary bike', 'Bicicleta estática'), ('stepmill machine', 'Escaladora'), ('tire', 'Neumático'), ('trap bar', 'Barra hexagonal'), ('upper body ergometer', 'Ergómetro de brazos'), ('weighted', 'Con lastre'), ('wheel roller', 'Rueda abdominal')], db_index=True, max_length=40, verbose_name='equipamiento')),
                ('instruction_steps', models.JSONField(blank=True, default=dict, help_text='Mapa idioma → lista de pasos. Se guardan los 10 idiomas del dataset.', verbose_name='pasos de ejecución')),
                ('image', models.ImageField(blank=True, upload_to='exercises/images/', verbose_name='foto')),
                ('animation', models.FileField(blank=True, upload_to='exercises/animations/', verbose_name='animación')),
                ('attribution', models.CharField(blank=True, help_text='Requisito de licencia del material visual: debe mostrarse junto a la imagen y no puede alterarse. Ver NOTICE.md.', max_length=255, verbose_name='atribución')),
                ('is_cardio', models.BooleanField(db_index=True, default=False, verbose_name='es cardio')),
                ('is_bodyweight', models.BooleanField(default=False, verbose_name='es de peso corporal')),
                ('is_global', models.BooleanField(db_index=True, default=True, verbose_name='del catálogo')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='custom_exercises', to=settings.AUTH_USER_MODEL, verbose_name='creado por')),
                ('secondary_muscles', models.ManyToManyField(blank=True, related_name='secondary_exercises', to='workouts.musclegroup', verbose_name='músculos secundarios')),
                ('target_muscle', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='primary_exercises', to='workouts.musclegroup', verbose_name='músculo objetivo')),
            ],
            options={
                'verbose_name': 'ejercicio',
                'verbose_name_plural': 'ejercicios',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Routine',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120, verbose_name='nombre')),
                ('description', models.TextField(blank=True, verbose_name='descripción')),
                ('is_active', models.BooleanField(db_index=True, default=True, verbose_name='activa')),
                ('source', models.CharField(choices=[('manual', 'Creada a mano'), ('ai', 'Generada por IA')], default='manual', max_length=16, verbose_name='origen')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='creada')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='actualizada')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='routines', to=settings.AUTH_USER_MODEL, verbose_name='usuario')),
            ],
            options={
                'verbose_name': 'rutina',
                'verbose_name_plural': 'rutinas',
                'ordering': ['-is_active', '-created_at'],
            },
        ),
        migrations.CreateModel(
            name='RoutineDay',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('weekday', models.IntegerField(choices=[(0, 'Lunes'), (1, 'Martes'), (2, 'Miércoles'), (3, 'Jueves'), (4, 'Viernes'), (5, 'Sábado'), (6, 'Domingo')], verbose_name='día')),
                ('name', models.CharField(blank=True, help_text='Ej.: Empuje, Pierna', max_length=80, verbose_name='nombre')),
                ('is_rest_day', models.BooleanField(default=False, verbose_name='día de descanso')),
                ('notes', models.TextField(blank=True, max_length=1000, verbose_name='notas')),
                ('routine', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='days', to='workouts.routine', verbose_name='rutina')),
            ],
            options={
                'verbose_name': 'día de rutina',
                'verbose_name_plural': 'días de rutina',
                'ordering': ['weekday'],
            },
        ),
        migrations.CreateModel(
            name='RoutineExercise',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.PositiveSmallIntegerField(default=0, verbose_name='orden')),
                ('target_sets', models.PositiveSmallIntegerField(default=3, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(20)], verbose_name='series')),
                ('target_reps_min', models.PositiveSmallIntegerField(default=8, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(100)], verbose_name='repeticiones (mín.)')),
                ('target_reps_max', models.PositiveSmallIntegerField(default=12, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(100)], verbose_name='repeticiones (máx.)')),
                ('target_rpe', models.DecimalField(blank=True, decimal_places=1, max_digits=3, null=True, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)], verbose_name='RPE objetivo')),
                ('rest_seconds', models.PositiveSmallIntegerField(default=90, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(900)], verbose_name='descanso (s)')),
                ('notes', models.TextField(blank=True, max_length=1000, verbose_name='notas')),
                ('exercise', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='+', to='workouts.exercise', verbose_name='ejercicio')),
                ('routine_day', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='exercises', to='workouts.routineday', verbose_name='día')),
            ],
            options={
                'verbose_name': 'ejercicio de la rutina',
                'verbose_name_plural': 'ejercicios de la rutina',
                'ordering': ['routine_day', 'order'],
            },
        ),
        migrations.CreateModel(
            name='WorkoutSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(db_index=True, verbose_name='fecha')),
                ('started_at', models.DateTimeField(blank=True, null=True, verbose_name='inicio')),
                ('finished_at', models.DateTimeField(blank=True, null=True, verbose_name='fin')),
                ('perceived_fatigue', models.PositiveSmallIntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)], verbose_name='fatiga percibida')),
                ('notes', models.TextField(blank=True, max_length=1000, verbose_name='notas')),
                ('routine_day', models.ForeignKey(blank=True, help_text='Qué día de la rutina se estaba haciendo, si se seguía alguna.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sessions', to='workouts.routineday', verbose_name='día de rutina')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sessions', to=settings.AUTH_USER_MODEL, verbose_name='usuario')),
            ],
            options={
                'verbose_name': 'sesión',
                'verbose_name_plural': 'sesiones',
                'ordering': ['-date'],
            },
        ),
        migrations.CreateModel(
            name='SetLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('set_number', models.PositiveSmallIntegerField(default=1, verbose_name='nº de serie')),
                ('weight_kg', models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(1000)], verbose_name='peso (kg)')),
                ('reps', models.PositiveSmallIntegerField(blank=True, null=True, validators=[django.core.validators.MaxValueValidator(1000)], verbose_name='repeticiones')),
                ('rpe', models.DecimalField(blank=True, decimal_places=1, max_digits=3, null=True, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)], verbose_name='RPE')),
                ('duration_seconds', models.PositiveIntegerField(blank=True, help_text='Para ejercicios de cardio.', null=True, verbose_name='duración (s)')),
                ('is_warmup', models.BooleanField(default=False, verbose_name='calentamiento')),
                ('completed', models.BooleanField(default=True, verbose_name='completada')),
                ('exercise', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='set_logs', to='workouts.exercise', verbose_name='ejercicio')),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sets', to='workouts.workoutsession', verbose_name='sesión')),
            ],
            options={
                'verbose_name': 'serie',
                'verbose_name_plural': 'series',
                'ordering': ['session', 'exercise', 'set_number'],
            },
        ),
        migrations.AddIndex(
            model_name='exercise',
            index=models.Index(fields=['body_part', 'equipment'], name='workouts_ex_body_pa_63e9d8_idx'),
        ),
        migrations.AddConstraint(
            model_name='routineday',
            constraint=models.UniqueConstraint(fields=('routine', 'weekday'), name='unique_day_per_routine'),
        ),
        migrations.AddIndex(
            model_name='workoutsession',
            index=models.Index(fields=['user', '-date'], name='workouts_wo_user_id_0f26ff_idx'),
        ),
        migrations.AddIndex(
            model_name='setlog',
            index=models.Index(fields=['exercise', 'session'], name='workouts_se_exercis_7d5810_idx'),
        ),
    ]
