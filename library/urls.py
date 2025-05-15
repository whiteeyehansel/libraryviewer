from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('entry/<int:entry_id>/', views.detail, name='detail'),
    path('entry/<int:entry_id>/open/', views.open_folder, name='open_folder'),
    path('settings/', views.settings_view, name='settings'),

    # For tooltip texture thumbnails and direct file serving
    path('serve-file/', views.serve_entry_file, name='serve_file'),  # legacy thumbnail loading
    path('serve-file/<int:entry_id>/<path:file>/', views.serve_entry_file_direct, name='serve_file_direct'),  # for model-viewer
]