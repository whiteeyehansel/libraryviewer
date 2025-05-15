from django.db import models

class FolderEntry(models.Model):
    name = models.CharField(max_length=255)
    path = models.TextField()
    jpeg_path = models.TextField(null=True, blank=True)
    gltf_path = models.TextField(null=True, blank=True)
    lnk_path = models.TextField(null=True, blank=True)
    obtained_on = models.DateTimeField(null=True, blank=True)  # ⬅️ new field

class AppSetting(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()