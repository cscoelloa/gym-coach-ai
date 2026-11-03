import django.contrib.auth.models
import django.contrib.auth.validators
import django.core.validators
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('goal', models.CharField(choices=[('bulk', 'Volumen'), ('cut', 'Definición'), ('maintain', 'Mantenimiento')], default='maintain', max_length=16, verbose_name='objetivo')),
                ('experience_level', models.CharField(choices=[('beginner', 'Principiante'), ('intermediate', 'Intermedio'), ('advanced', 'Avanzado')], default='beginner', max_length=16, verbose_name='nivel de experiencia')),
                ('sex', models.CharField(blank=True, choices=[('female', 'Mujer'), ('male', 'Hombre'), ('other', 'Otro'), ('undisclosed', 'Prefiero no decirlo')], default='undisclosed', max_length=16, verbose_name='sexo')),
                ('birth_date', models.DateField(blank=True, null=True, verbose_name='fecha de nacimiento')),
                ('height_cm', models.PositiveSmallIntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(100), django.core.validators.MaxValueValidator(250)], verbose_name='altura (cm)')),
                ('target_weight_kg', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True, validators=[django.core.validators.MinValueValidator(30), django.core.validators.MaxValueValidator(400)], verbose_name='peso objetivo (kg)')),
                ('weekly_weight_change_target_kg', models.DecimalField(blank=True, decimal_places=2, help_text='Positivo para ganar, negativo para perder. Ej.: 0.25 o -0.50', max_digits=4, null=True, validators=[django.core.validators.MinValueValidator(-2), django.core.validators.MaxValueValidator(2)], verbose_name='cambio de peso semanal objetivo (kg)')),
                ('available_days_per_week', models.PositiveSmallIntegerField(default=3, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(7)], verbose_name='días disponibles por semana')),
                ('available_equipment', models.JSONField(blank=True, default=list, help_text='Lista de tipos de equipamiento del catálogo. Vacío = sin restricción.', verbose_name='equipamiento disponible')),
                ('injuries_notes', models.TextField(blank=True, help_text='Este texto se le pasa a la IA como dato, nunca como instrucción.', max_length=500, validators=[django.core.validators.MaxLengthValidator(500)], verbose_name='lesiones y limitaciones')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'usuario',
                'verbose_name_plural': 'usuarios',
                'abstract': False,
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
    ]
