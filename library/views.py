from django.shortcuts import render, get_object_or_404
from .models import FolderEntry, AppSetting
from django.http import JsonResponse, FileResponse, Http404
from django.core.paginator import Paginator
from django.conf import settings
from django.contrib import messages
from django.apps import apps
from pathlib import Path
from PIL import Image
from urllib.parse import unquote
from django.urls import reverse

import json
import os



def index(request):
    q = request.GET.get('q', '')
    page = request.GET.get('page', 1)
    qs = FolderEntry.objects.filter(name__icontains=q) if q else FolderEntry.objects.all()
    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(page)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'library/partials/_entries.html',
                      {'entries': page_obj, 'MEDIA_URL': settings.MEDIA_URL})

    return render(request, 'library/index.html',
                  {'entries': page_obj, 'query': q, 'MEDIA_URL': settings.MEDIA_URL})

def serve_entry_file_direct(request, entry_id, file):
    entry = get_object_or_404(FolderEntry, id=entry_id)
    safe_path = os.path.normpath(os.path.join(entry.path, file))

    if not safe_path.startswith(entry.path) or not os.path.exists(safe_path):
        raise Http404("File not found or invalid path")

    return FileResponse(open(safe_path, 'rb'), content_type='application/octet-stream')

def detail(request, entry_id):
    entry = get_object_or_404(FolderEntry, id=entry_id)
    image_exists = os.path.exists(os.path.join(settings.MEDIA_ROOT, entry.jpeg_path or ''))
    gltf_info = analyze_gltf_and_textures(entry)

    for tex in gltf_info['textures']:
        tex_rel        = f"textures/{tex['name']}"
        tex['preview'] = reverse('serve_file_direct', args=[entry.id, tex_rel])

    # relative gltf path (models/scene.gltf, etc.)
    gltf_rel_path = ''
    if entry.gltf_path and entry.path in entry.gltf_path:
        gltf_rel_path = os.path.relpath(entry.gltf_path, entry.path).replace('\\', '/')

    # clean base URL: /serve-file/<id>/
    dummy = reverse('serve_file_direct', args=[entry.id, 'dummy.txt']).rstrip('/')  # /serve-file/13/dummy.txt
    base_url = dummy.rsplit('/', 1)[0] + '/'                                       # /serve-file/13/

    return render(request, 'library/detail.html', {
        'entry'        : entry,
        'MEDIA_URL'    : settings.MEDIA_URL,
        'image_exists' : image_exists,
        'gltf_info'    : gltf_info,
        'gltf_rel_path': gltf_rel_path,
        'base_url'     : base_url,
    })

def open_folder(request, entry_id):
    entry = get_object_or_404(FolderEntry, id=entry_id)
    try:
        os.startfile(entry.path)
        return JsonResponse({'status': 'ok'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

def settings_view(request):
    setting, _ = AppSetting.objects.get_or_create(key='ROOT_DIR')
    if request.method == 'POST':
        setting.value = request.POST['root'].strip()
        setting.save()
        messages.success(request, 'Root folder path updated.')
        if request.POST.get('action') == 'resync':
            apps.get_app_config('library').sync_folders()
            messages.success(request, 'Re-synced successfully.')
    return render(request, 'library/settings.html', {'root': setting.value})

TEX_MAP_TYPES = {
    "diffuse": "Diffuse", "albedo": "Albedo", "basecolor": "Base Color",
    "normal": "Normal", "bump": "Bump", "roughness": "Roughness",
    "metallic": "Metallic", "glossiness": "Glossiness", "specular": "Specular",
    "opacity": "Opacity", "emissive": "Emissive", "ao": "Ambient Occlusion",
    "occlusion": "Ambient Occlusion"
}

def analyze_gltf_and_textures(entry):
    info = {'file_size':None,'mesh_count':0,'vertex_count':0,'triangle_count':0,
            'textures':[],'texture_count':0}
    try:
        p = Path(entry.gltf_path)
        if p.exists():
            info['file_size'] = round(p.stat().st_size/1048576,2)
            data = json.load(p.open('r',encoding='utf-8'))
            info['mesh_count'] = len(data.get('meshes',[]))
            for acc in data.get('accessors',[]):
                if acc.get('type')=='SCALAR' and 'count' in acc:
                    info['vertex_count'] += acc['count']
            info['triangle_count'] = int(info['vertex_count']*0.5)
    except Exception: pass

    tex_dir = Path(entry.path)/'textures'
    if tex_dir.exists():
        for tex in tex_dir.glob('*.png'):
            kind = next((v for k,v in TEX_MAP_TYPES.items() if k in tex.name.lower()),'unknown')
            try:  w,h = Image.open(tex).size
            except Exception: w=h='?'
            info['textures'].append({
                'name':tex.name, 'type':kind,
                'size':round(tex.stat().st_size/1048576,2),
                'dimensions':f'{w}×{h}'
            })
        info['texture_count']=len(info['textures'])
    return info

def serve_entry_file(request):
    entry_id = request.GET.get('entry_id')
    rel_path = request.GET.get('file')

    if not entry_id or not rel_path:
        raise Http404("Invalid parameters")

    entry = get_object_or_404(FolderEntry, id=entry_id)
    full_path = os.path.normpath(os.path.join(entry.path, unquote(rel_path)))

    if not full_path.startswith(entry.path):
        raise Http404("Invalid path")

    if not os.path.isfile(full_path):
        raise Http404("File not found")

    return FileResponse(open(full_path, 'rb'), content_type='application/octet-stream')

