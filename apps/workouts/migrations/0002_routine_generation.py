import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('aiassist', '0001_initial'),
        ('workouts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='routine',
            name='generation',
            field=models.ForeignKey(blank=True, help_text='Qué llamada a la IA produjo esta rutina, si fue generada.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='routines', to='aiassist.aigeneration', verbose_name='generación'),
        ),
    ]
