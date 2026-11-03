web: sh scripts/start-web.sh
worker: env DJANGO_SETTINGS_MODULE=config.settings.prod celery -A config worker -l info
beat: env DJANGO_SETTINGS_MODULE=config.settings.prod celery -A config beat -l info
