import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('aiassist', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('kind', models.CharField(choices=[('stall_detected', 'Estancamiento detectado'), ('weight_off_track', 'Peso fuera de objetivo'), ('progress_ready', 'Análisis de progreso listo'), ('routine_ready', 'Rutina lista')], db_index=True, max_length=32, verbose_name='tipo')),
                ('severity', models.CharField(choices=[('info', 'Información'), ('warning', 'Atención')], default='info', max_length=16, verbose_name='importancia')),
                ('title', models.CharField(max_length=200, verbose_name='título')),
                ('body', models.TextField(verbose_name='contenido')),
                ('payload', models.JSONField(blank=True, default=dict, help_text='Detalle estructurado para la interfaz.', verbose_name='datos')),
                ('is_read', models.BooleanField(db_index=True, default=False, verbose_name='leída')),
                ('emailed_at', models.DateTimeField(blank=True, null=True, verbose_name='enviada por correo')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='fecha')),
                ('generation', models.ForeignKey(blank=True, help_text='Qué llamada a la IA la produjo, si vino de ahí.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='notifications', to='aiassist.aigeneration', verbose_name='generación')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to=settings.AUTH_USER_MODEL, verbose_name='usuario')),
            ],
            options={
                'verbose_name': 'notificación',
                'verbose_name_plural': 'notificaciones',
                'ordering': ['-created_at'],
                'indexes': [models.Index(fields=['user', 'is_read', '-created_at'], name='notificatio_user_id_f2ad08_idx')],
            },
        ),
    ]
