import os
import re
import shutil
import unicodedata
from datetime import datetime
from pathlib import Path

from django.apps        import AppConfig, apps
from django.conf        import settings
from django.core.management import call_command
from django.db          import connections
from django.db.utils    import OperationalError
from django.utils.timezone import make_aware
from dotenv             import load_dotenv


class LibraryConfig(AppConfig):
    """ Registers the “library” Django app and kicks off a one-time folder sync. """
    name = "library"

    # ────────────────────────────────────────────────
    # Django calls this once the registry is built
    # ────────────────────────────────────────────────
    def ready(self):
        # ▸ When runserver’s autoreloader forks a child it sets RUN_MAIN=’true’.
        if os.environ.get("RUN_MAIN") != "true":
            return

        # 1️⃣  Make sure the DB is actually up.
        try:
            connections["default"].ensure_connection()
        except OperationalError:
            print("[Library] DB not ready — skipping sync.")
            return

        # 2️⃣  Run migrations silently (handy in dev / fresh clones).
        try:
            call_command("makemigrations", "library", interactive=False, verbosity=0)
            call_command("migrate",        interactive=False, verbosity=0)
        except Exception as exc:
            print(f"[Library] Migration error: {exc}")
            return

        # 3️⃣  Load .env for VERSION & default root path.
        load_dotenv()
        settings.APP_VERSION = os.getenv("APP_VERSION", "dev")

        # 4️⃣  Grab our models *after* the registry is ready.
        ModelType    = apps.get_model("library", "ModelType")
        AppSetting   = apps.get_model("library", "AppSetting")
        FolderEntry  = apps.get_model("library", "FolderEntry")

        # 5️⃣  Ensure we have a ROOT_DIR setting.
        default_root = os.getenv("DEFAULT_ROOT_DIR", r"C:\Fallback\Downloads")
        AppSetting.objects.get_or_create(key="ROOT_DIR", defaults={"value": default_root})

        # 6️⃣  Ensure the “glTF” type exists (others can be added later).
        gltf_type, _ = ModelType.objects.get_or_create(code="gltf", defaults={"name": "glTF"})

        # 7️⃣  Do the folder synchronisation.
        try:
            self.sync_folders(
                root_dir   = Path(AppSetting.objects.get(key="ROOT_DIR").value).expanduser(),
                entry_cls  = FolderEntry,
                type_gltf  = gltf_type
            )
        except Exception as exc:
            print(f"[Library] Folder sync failed: {exc}")

    # ────────────────────────────────────────────────
    # Sync helper
    # ────────────────────────────────────────────────
    def sync_folders(self, *, root_dir: Path, entry_cls, type_gltf):
        """Scans `root_dir`, (re-)creates FolderEntry rows and copies thumbnails."""
        if not root_dir.exists():
            print(f"[Library] ROOT_DIR {root_dir} missing — aborting sync.")
            return

        thumb_dir = Path(settings.MEDIA_ROOT) / "thumbs"
        thumb_dir.mkdir(parents=True, exist_ok=True)

        # Snapshot of existing DB rows keyed by folder-name
        existing = {e.name: e for e in entry_cls.objects.all()}
        seen     = set()

        print(f"[Library] Scanning {root_dir} …")

        for folder in sorted(p for p in root_dir.iterdir() if p.is_dir()):
            name = folder.name
            jpeg = folder / f"{name}.jpeg"
            gltf = folder / f"{name}.gltf"
            urlf = folder / f"{name}.url"

            if not jpeg.exists():
                continue                                    # must have thumbnail

            # Copy thumbnail if newer / missing
            safe_name   = self.slugify(name)
            dest_thumb  = thumb_dir / f"{safe_name}.jpeg"
            if self.needs_copy(dest_thumb, jpeg):
                shutil.copyfile(jpeg, dest_thumb)
                print(f"  • thumbnail updated: {name}")

            # Prepare/lookup DB row
            entry   = existing.get(name)
            mtime   = make_aware(datetime.fromtimestamp(gltf.stat().st_mtime)) if gltf.exists() else None
            url_val = self.parse_url(urlf)

            if entry is None:
                entry_cls.objects.create(
                    name        = name,
                    path        = str(folder),
                    jpeg_path   = f"thumbs/{safe_name}.jpeg",
                    gltf_path   = str(gltf) if gltf.exists() else None,
                    lnk_path    = url_val,
                    obtained_on = mtime,
                    type        = type_gltf,   # default type
                )
                print(f"  + added: {name}")
            else:
                changed = False
                if entry.jpeg_path != f"thumbs/{safe_name}.jpeg":
                    entry.jpeg_path = f"thumbs/{safe_name}.jpeg"; changed = True
                if gltf.exists() and entry.gltf_path != str(gltf):
                    entry.gltf_path = str(gltf);           changed = True
                if entry.lnk_path != url_val:
                    entry.lnk_path = url_val;              changed = True
                if mtime and entry.obtained_on != mtime:
                    entry.obtained_on = mtime;             changed = True
                if entry.type_id is None:
                    entry.type = type_gltf;                changed = True
                if changed:
                    entry.save()
                    print(f"  • updated: {name}")

            seen.add(name)

        # Purge orphans
        for lost_name in set(existing) - seen:
            existing[lost_name].delete()
            print(f"  – removed orphan: {lost_name}")

        print("[Library] Folder sync complete.")

    # ────────────────────────────────────────────────
    # Helpers
    # ────────────────────────────────────────────────
    @staticmethod
    def slugify(text: str) -> str:
        text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
        text = re.sub(r"[^\w\-. ]+", "", text).strip().replace(" ", "_")
        return text.lower()

    @staticmethod
    def needs_copy(dest: Path, src: Path) -> bool:
        try:
            return not dest.exists() or dest.stat().st_mtime != src.stat().st_mtime
        except OSError:
            return True

    @staticmethod
    def parse_url(url_file: Path) -> str | None:
        if not url_file.exists():
            return None
        try:
            with url_file.open("r", encoding="utf-8") as fh:
                for line in fh:
                    if line.lower().startswith("url="):
                        return line.strip().split("=", 1)[1]
        except Exception:
            pass
        return None