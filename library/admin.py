from django.contrib import admin
from .models import ModelType, ModelCategory, Tag, FolderEntry
# Register your models here.
admin.site.register([ModelType, ModelCategory, Tag, FolderEntry])