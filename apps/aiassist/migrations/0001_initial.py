import apps.aiassist.fields
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
            name='AIProviderConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('provider', models.CharField(choices=[('anthropic', 'Anthropic (Claude)'), ('openai', 'OpenAI'), ('google', 'Google Gemini')], max_length=16, verbose_name='proveedor')),
                ('model', models.CharField(blank=True, help_text='Identificador exacto del modelo. Para Anthropic, dejarlo vacío usa `claude-opus-5`. Para OpenAI y Google, consulta la documentación del proveedor: un identificador inventado devuelve 404.', max_length=64, verbose_name='modelo')),
                ('api_key', apps.aiassist.fields.EncryptedTextField(help_text='Se guarda cifrada. Después de guardarla solo se mostrará enmascarada.', verbose_name='API key')),
                ('max_tokens', models.PositiveIntegerField(default=16000, help_text='Tope de salida. Lo fija el admin, nunca el usuario: es control de gasto.', validators=[django.core.validators.MinValueValidator(256), django.core.validators.MaxValueValidator(128000)], verbose_name='máximo de tokens')),
                ('effort', models.CharField(blank=True, choices=[('low', 'Bajo'), ('medium', 'Medio'), ('high', 'Alto'), ('xhigh', 'Muy alto'), ('max', 'Máximo')], help_text='Solo lo soportan algunos modelos. Vacío = el valor por defecto del proveedor.', max_length=8, verbose_name='esfuerzo')),
                ('timeout_seconds', models.PositiveSmallIntegerField(default=120, verbose_name='tiempo de espera (s)')),
                ('is_active', models.BooleanField(default=True, help_text='Al activar una, las demás se desactivan automáticamente.', verbose_name='activa')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='creada')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='actualizada')),
            ],
            options={
                'verbose_name': 'configuración de IA',
                'verbose_name_plural': 'configuraciones de IA',
                'ordering': ['-is_active', '-updated_at'],
            },
        ),
        migrations.CreateModel(
            name='VectorStore',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120, verbose_name='nombre')),
                ('description', models.TextField(blank=True, verbose_name='descripción')),
                ('openai_vector_store_id', models.CharField(blank=True, help_text='Se rellena al crearlo en OpenAI.', max_length=64, verbose_name='id en OpenAI')),
                ('is_active', models.BooleanField(default=True, verbose_name='activo')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='creado')),
            ],
            options={
                'verbose_name': 'almacén vectorial',
                'verbose_name_plural': 'almacenes vectoriales',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='PromptTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(choices=[('routine_generation', 'Generación de rutinas'), ('progress_analysis', 'Análisis de progreso'), ('weight_analysis', 'Análisis de peso')], db_index=True, max_length=32, verbose_name='tipo')),
                ('name', models.CharField(max_length=120, verbose_name='nombre')),
                ('system_prompt', models.TextField(verbose_name='instrucciones de sistema')),
                ('user_template', models.TextField(help_text='Plantilla de Django. Las variables disponibles aparecen debajo.', verbose_name='plantilla del mensaje')),
                ('version', models.PositiveSmallIntegerField(default=1, verbose_name='versión')),
                ('is_active', models.BooleanField(default=True, verbose_name='activa')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='creada')),
            ],
            options={
                'verbose_name': 'prompt',
                'verbose_name_plural': 'prompts',
                'ordering': ['key', '-version'],
                'constraints': [models.UniqueConstraint(fields=('key', 'version'), name='unique_prompt_version')],
            },
        ),
        migrations.CreateModel(
            name='KnowledgeDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='título')),
                ('file', models.FileField(upload_to='knowledge/', verbose_name='archivo')),
                ('openai_file_id', models.CharField(blank=True, max_length=64, verbose_name='id de archivo en OpenAI')),
                ('status', models.CharField(choices=[('pending', 'Pendiente'), ('indexing', 'Indexando'), ('indexed', 'Indexado'), ('failed', 'Fallido')], db_index=True, default='pending', max_length=16, verbose_name='estado')),
                ('error', models.TextField(blank=True, verbose_name='error')),
                ('attributes', models.JSONField(blank=True, default=dict, help_text='Metadatos para filtrar en la búsqueda. Máximo 16 claves.', verbose_name='atributos')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='subido')),
                ('uploaded_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='subido por')),
                ('vector_store', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='aiassist.vectorstore', verbose_name='almacén')),
            ],
            options={
                'verbose_name': 'documento',
                'verbose_name_plural': 'documentos',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='AIGeneration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('kind', models.CharField(choices=[('routine', 'Rutina'), ('progress', 'Análisis de progreso'), ('weight', 'Análisis de peso'), ('test', 'Prueba de configuración')], db_index=True, max_length=16, verbose_name='tipo')),
                ('provider', models.CharField(max_length=16, verbose_name='proveedor')),
                ('model', models.CharField(max_length=64, verbose_name='modelo')),
                ('prompt_rendered', models.TextField(blank=True, verbose_name='prompt enviado')),
                ('raw_response', models.TextField(blank=True, verbose_name='respuesta cruda')),
                ('parsed_output', models.JSONField(blank=True, null=True, verbose_name='salida validada')),
                ('input_tokens', models.PositiveIntegerField(default=0, verbose_name='tokens de entrada')),
                ('output_tokens', models.PositiveIntegerField(default=0, verbose_name='tokens de salida')),
                ('latency_ms', models.PositiveIntegerField(default=0, verbose_name='latencia (ms)')),
                ('status', models.CharField(choices=[('ok', 'Correcta'), ('error', 'Error'), ('refused', 'Rechazada por el modelo')], default='ok', max_length=16, verbose_name='estado')),
                ('error', models.TextField(blank=True, verbose_name='error')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='fecha')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ai_generations', to=settings.AUTH_USER_MODEL, verbose_name='usuario')),
            ],
            options={
                'verbose_name': 'generación',
                'verbose_name_plural': 'generaciones',
                'ordering': ['-created_at'],
                'indexes': [models.Index(fields=['user', 'kind', '-created_at'], name='aiassist_ai_user_id_81f02d_idx')],
            },
        ),
    ]
