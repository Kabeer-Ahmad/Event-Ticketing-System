from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        import core.middleware  # This will register the middleware signals
        import core.signals     # This will register the QR code generation signals
