from django.apps import AppConfig


class IngestionWorkerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ingestion_worker'
