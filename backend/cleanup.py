import os
import shutil
import subprocess
import platform

_system = platform.system()


def _dir_size(path: str) -> int:
    """Fast directory size via `du`, falls back to os.walk."""
    if not os.path.exists(path):
        return 0
    try:
        if _system in ('Darwin', 'Linux'):
            r = subprocess.run(
                ['du', '-sk', path],
                capture_output=True, text=True, timeout=10
            )
            if r.returncode == 0 and r.stdout:
                return int(r.stdout.split('\t')[0]) * 1024
        elif _system == 'Windows':
            r = subprocess.run(
                ['powershell', '-NoProfile', '-Command',
                 f'(Get-ChildItem -Path "{path}" -Recurse -ErrorAction SilentlyContinue | '
                 f'Measure-Object -Property Length -Sum).Sum'],
                capture_output=True, text=True, shell=True, timeout=20
            )
            val = r.stdout.strip()
            if val and val.replace('.', '', 1).isdigit():
                return int(float(val))
    except Exception:
        pass
    # Python fallback
    total = 0
    for root, _, files in os.walk(path, onerror=lambda _: None):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return total


def _fmt(b: int) -> str:
    if b >= 1024 ** 3:
        return f'{b / (1024 ** 3):.1f} GB'
    if b >= 1024 ** 2:
        return f'{b / (1024 ** 2):.0f} MB'
    return f'{b / 1024:.0f} KB'


def _candidate_paths() -> list:
    if _system == 'Darwin':
        return [
            {
                'id':   'user_caches',
                'name': 'Cache de Aplicativos',
                'path': os.path.expanduser('~/Library/Caches'),
                'desc': 'Cache gerado pelos apps do utilizador',
                'icon': 'ti-stack',
            },
            {
                'id':   'user_logs',
                'name': 'Logs de Aplicativos',
                'path': os.path.expanduser('~/Library/Logs'),
                'desc': 'Ficheiros de log do utilizador',
                'icon': 'ti-file-text',
            },
            {
                'id':   'trash',
                'name': 'Lixeira',
                'path': os.path.expanduser('~/.Trash'),
                'desc': 'Ficheiros aguardando exclusão definitiva',
                'icon': 'ti-trash',
            },
        ]
    if _system == 'Windows':
        return [
            {
                'id':   'user_temp',
                'name': 'Temporários do Utilizador',
                'path': os.environ.get('TEMP', r'C:\Users\Default\AppData\Local\Temp'),
                'desc': '%TEMP% — arquivos temporários do utilizador',
                'icon': 'ti-file-x',
            },
            {
                'id':   'system_temp',
                'name': 'Temporários do Sistema',
                'path': r'C:\Windows\Temp',
                'desc': 'C:\\Windows\\Temp — requer Administrador',
                'icon': 'ti-brand-windows',
            },
        ]
    return []


def get_cleanable_items() -> list:
    result = []
    for c in _candidate_paths():
        path = c['path']
        if not path or not os.path.exists(path):
            continue
        size = _dir_size(path)
        result.append({**c, 'size_bytes': size, 'size_label': _fmt(size)})
    return result


def clean_item(item_id: str) -> dict:
    items = get_cleanable_items()
    item  = next((i for i in items if i['id'] == item_id), None)
    if not item:
        return {'success': False, 'message': 'Item não encontrado.', 'freed_bytes': 0}

    freed = item['size_bytes']
    path  = item['path']
    errors = 0

    try:
        for entry in os.scandir(path):
            try:
                if entry.is_dir(follow_symlinks=False):
                    shutil.rmtree(entry.path, ignore_errors=True)
                else:
                    os.remove(entry.path)
            except Exception:
                errors += 1
    except Exception as e:
        return {'success': False, 'message': str(e), 'freed_bytes': 0}

    msg = f'"{item["name"]}" limpo — {item["size_label"]} liberados.'
    if errors:
        msg += f' ({errors} ficheiro(s) em uso ignorados.)'
    return {'success': True, 'message': msg, 'freed_bytes': freed}
