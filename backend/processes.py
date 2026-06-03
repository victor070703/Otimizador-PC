import psutil
import platform
import threading
import time
import copy

_system = platform.system()

_PROCESS_ICONS = {
    'chrome':       'ti-brand-chrome',
    'firefox':      'ti-brand-firefox',
    'safari':       'ti-brand-safari',
    'discord':      'ti-brand-discord',
    'spotify':      'ti-brand-spotify',
    'code':         'ti-brand-vscode',
    'cursor':       'ti-brand-vscode',
    'python':       'ti-brand-python',
    'python3':      'ti-brand-python',
    'node':         'ti-brand-nodejs',
    'steam':        'ti-brand-steam',
    'slack':        'ti-brand-slack',
    'zoom':         'ti-video',
    'teams':        'ti-brand-teams',
    'outlook':      'ti-mail',
    'word':         'ti-file-word',
    'excel':        'ti-file-spreadsheet',
    'figma':        'ti-brand-figma',
    'terminal':     'ti-terminal',
    'iterm':        'ti-terminal-2',
    'finder':       'ti-folder',
    'explorer':     'ti-folder',
    'onedrive':     'ti-cloud',
    'dropbox':      'ti-brand-dropbox',
    'obs':          'ti-video',
    'whatsapp':     'ti-brand-whatsapp',
    'telegram':     'ti-brand-telegram',
}


def _get_icon(name: str) -> str:
    lower = name.lower().replace('.exe', '')
    for key, icon in _PROCESS_ICONS.items():
        if key in lower:
            return icon
    return 'ti-app-window'


def _format_ram(bytes_val: float) -> str:
    mb = bytes_val / (1024 ** 2)
    if mb >= 1024:
        return f'{round(mb / 1024, 1)} GB'
    return f'{round(mb)} MB'


# ── Background process cache ──────────────────────────────────────────────────
# Psutil's cpu_percent() always returns 0.0 on the very first call per process.
# A background thread samples continuously so the API always returns real values.

_cache: list = []
_cache_lock  = threading.Lock()


def _build_snapshot() -> dict:
    """Build a {pid: proc_obj} map with cpu_percent initialised (non-blocking)."""
    snapshot = {}
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'status']):
        try:
            info = proc.info
            if not info.get('memory_info'):
                continue
            snapshot[info['pid']] = {
                'pid':       info['pid'],
                'name':      info['name'] or 'Desconhecido',
                'cpu':       round(info['cpu_percent'] or 0.0, 1),
                'ram_bytes': info['memory_info'].rss,
                'ram_label': _format_ram(info['memory_info'].rss),
                'status':    info.get('status', ''),
                'icon':      _get_icon(info['name'] or ''),
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return snapshot


def _update_loop():
    # First pass: just initialise cpu_percent counters (values will be 0)
    _build_snapshot()
    time.sleep(1)

    while True:
        try:
            snapshot = _build_snapshot()
            procs = list(snapshot.values())
            procs.sort(key=lambda p: p['cpu'] * 10 + p['ram_bytes'] / (1024 ** 2), reverse=True)
            with _cache_lock:
                _cache.clear()
                _cache.extend(procs)
        except Exception:
            pass
        time.sleep(2)


_bg_thread = threading.Thread(target=_update_loop, daemon=True)
_bg_thread.start()
# ─────────────────────────────────────────────────────────────────────────────


def get_processes(limit: int = 25) -> list:
    with _cache_lock:
        return copy.deepcopy(_cache[:limit])


def kill_process(pid: int) -> dict:
    try:
        proc = psutil.Process(pid)
        name = proc.name()
        proc.terminate()
        return {'success': True, 'message': f'"{name}" encerrado com sucesso.'}
    except psutil.NoSuchProcess:
        return {'success': False, 'message': 'Processo não encontrado.'}
    except psutil.AccessDenied:
        return {'success': False, 'message': 'Sem permissão para encerrar este processo.'}
    except Exception as e:
        return {'success': False, 'message': str(e)}
