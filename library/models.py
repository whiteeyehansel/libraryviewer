from django.db import models


class ModelType(models.Model):
    """
    High-level format family (GLTF, HDR, OBJ, …).

    ─ code – machine-friendly key, unique (e.g. “gltf”)
    ─ name – human label (“glTF 2.0”)
    """
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Model Type"
        verbose_name_plural = "Model Types"
        ordering = ["code"]

    def __str__(self) -> str:              # pragma: no cover
        return self.name


class ModelCategory(models.Model):
    """
    User-defined bucket inside a given ModelType:
    e.g. “Buildings”, “Vehicles” (for type =gltf).
    """
    name = models.CharField(max_length=100)
    type = models.ForeignKey(
        ModelType,
        on_delete=models.CASCADE,
        related_name="categories",
    )

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        unique_together = ("name", "type")
        ordering = ["type__code", "name"]

    def __str__(self) -> str:              # pragma: no cover
        return f"{self.name} ({self.type.code})"


class Tag(models.Model):
    """
    Free-form labels a user can attach to any FolderEntry,
    e.g. “low-poly”, “PBR”, “scan”.
    """
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:              # pragma: no cover
        return self.name


class FolderEntry(models.Model):
    """
    One on-disk asset folder (thumbnail + model + optional .url link).
    """
    name        = models.CharField(max_length=255)
    path        = models.TextField()                           # absolute FS path
    jpeg_path   = models.TextField(null=True, blank=True)      # MEDIA-relative
    gltf_path   = models.TextField(null=True, blank=True)      # same
    lnk_path    = models.TextField(null=True, blank=True)      # web link
    obtained_on = models.DateTimeField(null=True, blank=True)  # FS mtime stamp

    type = models.ForeignKey(                                 # GLTF / HDR / …
        ModelType,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="entries",
    )
    category = models.ForeignKey(                             # optional bucket
        ModelCategory,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="entries",
    )
    tags = models.ManyToManyField(Tag, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Folder Entry"
        verbose_name_plural = "Folder Entries"

    def __str__(self) -> str:              # pragma: no cover
        return self.name

class AppSetting(models.Model):            # ← add this block
    key   = models.CharField(max_length=100, unique=True)
    value = models.TextField()

    def __str__(self):
        return f"{self.key}={self.value}"