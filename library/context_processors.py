from django.conf import settings
from .models import ModelType, ModelCategory, Tag

def app_version(request):
    return {
        'VERSION': getattr(settings, 'APP_VERSION', 'dev')
    }


def sidebar_context(request):
    return {
        'types': ModelType.objects.all(),
        'categories': ModelCategory.objects.all(),
        'tags': Tag.objects.all(),
    }