from django.urls import path
from . import views

urlpatterns = [
    # ───────────────────────────────
    # Core browser
    # ───────────────────────────────
    path("", views.index,          name="index"),
    path("entry/<int:entry_id>/", views.detail,        name="detail"),
    path("entry/<int:entry_id>/open/", views.open_folder, name="open_folder"),

    # ───────────────────────────────
    # Settings page
    # ───────────────────────────────
    path("settings/", views.settings_view, name="settings"),

    # ───────────────────────────────
    # Dynamic assets (thumbnails / GLTF / textures)
    # ───────────────────────────────
    path("serve-file/", views.serve_entry_file,       name="serve_file"),         # legacy query-string endpoint
    path("serve-file/<int:entry_id>/<path:file>/", views.serve_entry_file_direct, name="serve_file_direct"), # prettified

    # ───────────────────────────────
    # (NEW) Browsing helpers — not yet wired in templates,
    # but handy for future side-menu filtering or API calls.
    # ───────────────────────────────
    path("type/<str:type_code>/", views.index, name="browse_by_type"),      # e.g. /type/gltf/
    path("category/<int:cat_id>/", views.index, name="browse_by_category"),  # e.g. /category/5/
]
