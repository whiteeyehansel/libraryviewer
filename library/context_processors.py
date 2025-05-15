from django.conf import settings

def app_version(request):
    return {
        'VERSION': getattr(settings, 'APP_VERSION', 'dev')
    }