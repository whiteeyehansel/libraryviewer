📝 ### LibraryViewer

LibraryViewer is a Django-powered web app for browsing local 3D asset folders.It supports .gltf model preview via <model-viewer>, texture tooltips, metadata extraction, and live disk-based syncing — no file copies needed.

🔧 Features

    📁 Infinite scroll of indexed asset folders

    🖼 Live texture thumbnails on hover

    📊 Mesh + texture analysis (polycount, formats, dimensions)

    🧱 <model-viewer>-powered GLTF viewer (pan, zoom, rotate)

    ⚡ Instant model streaming — no asset copies needed

    🛠 Built-in settings panel to change root folder + resync

📂 Folder Structure

    Each asset must follow this layout inside the configured root:

    /<ASSET_NAME>/
        ├─ <ASSET_NAME>.gltf
        ├─ <ASSET_NAME>.jpeg
        ├─ textures/
        │   ├─ albedo.png
        │   ├─ normal.png
        │   └─ ...
        └─ <ASSET_NAME>.url  ← optional internet shortcut

🚀 Getting Started

    Clone the repo:

    git clone https://github.com/youruser/libraryviewer.git
    cd libraryviewer

    Setup a virtualenv:

    python -m venv .venv
    .\.venv\Scripts\activate

    Install requirements:

    pip install -r requirements.txt

    Create .env with default root folder:

    DEFAULT_ROOT_DIR=ADD_DEFAULT_PATH_HERE

    Start server:

    python manage.py runserver

🔑 Admin Access (optional)

    To enable Django admin:

    python manage.py createsuperuser

📌 TODOs

    Enable asset tagging
    Add ZIP export for entire assets
    Add categories
    Better search / filter / sorting
    Add .HDR support
    Add .OBJ support
    Add .FBX support
    Add .BLEND support
    Add users / profiles / authentication (maybe)
    Add logging
    Add more stats in index page card
    Add a proper sidebar
    Add a proper footer
    Add a proper menu
    Auto-render thumbnails if none are present
    Make the modal of the 3D viewer actually look presentable
    Proper js / css



📦 Built With

    Django

    Bootstrap 5

    <model-viewer>

    Pillow

Pure Python — no JS frameworks

🧠 Author - This is the only part written by a human in the entire repo.

I got bored so one day I decided to play with this "vibe coding" and AI Agent building apps.
This is what came out.
I have not written a single line of code for this app.
All code is written by a whole bunch of LLM models and a variety of agent experiments, apps, automations, and whatever I could think of.


