from django.apps import AppConfig
import os
import shutil
import unicodedata
import re
from django.conf import settings
from datetime import datetime
from dotenv import load_dotenv
from django.utils.timezone import make_aware


class LibraryConfig(AppConfig):
    name = 'library'

    def ready(self):
        if os.environ.get('RUN_MAIN') != 'true':
            return

        from django.db import connections
        from django.db.utils import OperationalError
        from django.core.management import call_command
        from django.apps import apps
        from dotenv import load_dotenv
        
        # 1. Check DB is up
        try:
            db_conn = connections['default']
            db_conn.ensure_connection()
        except OperationalError:
            print("[Sync] Database not ready yet. Skipping sync.")
            return

        # 2. Auto-run migrations
        try:
            call_command('makemigrations', 'library', interactive=False, verbosity=0)
            call_command('migrate', interactive=False, verbosity=0)
        except Exception as e:
            print(f"[Sync] Migration error: {e}")
            return

        # 3. Load env for fallback
        load_dotenv()
        from django.apps import apps
        AppSetting = apps.get_model('library', 'AppSetting')

        default_dir = os.getenv('DEFAULT_ROOT_DIR', r'C:\Fallback\Downloads')
        setting, created = AppSetting.objects.get_or_create(key='ROOT_DIR', defaults={'value': default_dir})
        if created:
            print(f"[Sync] ROOT_DIR initialized from .env: {default_dir}")

        # 4. Run sync
        try:
            self.sync_folders()
        except Exception as e:
            print(f"[Sync] Failed to run folder sync: {e}")

    

    def sync_folders(self):
        from django.apps import apps
        FolderEntry = apps.get_model('library', 'FolderEntry')
        AppSetting = apps.get_model('library', 'AppSetting')

        root_dir = AppSetting.objects.get(key='ROOT_DIR').value.strip()
        if not root_dir or not os.path.exists(root_dir):
            print(f"[Sync] Invalid or missing ROOT_DIR: {root_dir}")
            return

        media_thumb_dir = os.path.join(settings.MEDIA_ROOT, 'thumbs')
        os.makedirs(media_thumb_dir, exist_ok=True)

        existing_entries = {e.name: e for e in FolderEntry.objects.all()}
        seen_names = set()
        renamed_map = {}

        print(f"[Sync] Scanning root folder: {root_dir}")

        for folder in os.listdir(root_dir):
            folder_path = os.path.join(root_dir, folder)
            if not os.path.isdir(folder_path):
                continue

            jpeg = os.path.join(folder_path, folder + '.jpeg')
            gltf = os.path.join(folder_path, folder + '.gltf')
            lnk = os.path.join(folder_path, folder + '.url')
            obtained_on = None

            if os.path.exists(gltf):
                obtained_on = make_aware(datetime.fromtimestamp(os.path.getmtime(gltf)))

            if not os.path.exists(jpeg):
                print(f"[Sync] Skipping {folder} — no JPEG found")
                continue

            safe_name = self.slugify_filename(folder)
            dest_jpeg = os.path.join(media_thumb_dir, safe_name + '.jpeg')
            jpeg_db_path = f'thumbs/{safe_name}.jpeg'

            if self.file_changed(dest_jpeg, jpeg):
                shutil.copyfile(jpeg, dest_jpeg)
                print(f"[Sync] Copied thumbnail for: {folder}")

            seen_names.add(folder)
            entry = existing_entries.get(folder)

            if not entry:
                FolderEntry.objects.create(
                    name=folder,
                    path=folder_path,
                    jpeg_path=jpeg_db_path,
                    gltf_path=gltf if os.path.exists(gltf) else None,
                    lnk_path=self.parse_url(lnk) if os.path.exists(lnk) else None,
                    obtained_on=obtained_on,
                )
                print(f"[Sync] Added new folder: {folder}")
            else:
                updated = False
                if entry.jpeg_path != jpeg_db_path:
                    entry.jpeg_path = jpeg_db_path
                    updated = True
                if os.path.exists(gltf) and entry.gltf_path != gltf:
                    entry.gltf_path = gltf
                    updated = True
                if os.path.exists(lnk):
                    new_url = self.parse_url(lnk)
                    if entry.lnk_path != new_url:
                        entry.lnk_path = new_url
                        updated = True
                if obtained_on and entry.obtained_on != obtained_on:
                    entry.obtained_on = obtained_on
                    updated = True
                if updated:
                    entry.save()
                    print(f"[Sync] Updated: {folder}")

        for name, entry in existing_entries.items():
            if name not in seen_names and name not in renamed_map:
                entry.delete()
                print(f"[Sync] Removed orphan: {name}")

        print("[Sync] Folder sync complete.")

    def slugify_filename(self, name):
        name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('ascii')
        name = re.sub(r'[^\w\-. ]', '', name)
        return name.replace(' ', '_')

    def file_changed(self, old_path, new_path):
        try:
            return not os.path.exists(old_path) or os.path.getmtime(old_path) != os.path.getmtime(new_path)
        except:
            return True

    def parse_url(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('URL='):
                        return line.split('=', 1)[1].strip()
        except Exception:
            pass
        return None