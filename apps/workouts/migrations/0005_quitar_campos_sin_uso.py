from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('workouts', '0004_rutinas_asignables_a_dias'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='routineexercise',
            name='notes',
        ),
        migrations.RemoveField(
            model_name='routineexercise',
            name='target_rpe',
        ),
        migrations.RemoveField(
            model_name='scheduleentry',
            name='notes',
        ),
        migrations.RemoveField(
            model_name='setlog',
            name='duration_seconds',
        ),
        migrations.RemoveField(
            model_name='workoutsession',
            name='perceived_fatigue',
        ),
    ]
