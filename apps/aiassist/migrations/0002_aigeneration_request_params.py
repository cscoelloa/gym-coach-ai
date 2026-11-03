from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('aiassist', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='aigeneration',
            name='request_params',
            field=models.JSONField(blank=True, default=dict, help_text='El reparto semanal que pidió la persona, para poder contrastarlo con la salida.', verbose_name='lo que se pidió'),
        ),
    ]
