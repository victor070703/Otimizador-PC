import psutil
import subprocess
import platform

_system = platform.system()

# ── Curated service list per platform ────────────────────────────────────────

_MACOS_SERVICES = [
    {
        'id': 'spotlight',
        'name': 'Spotlight',
        'process': 'mds_stores',
        'launchctl': 'com.apple.metadata.mds',
        'desc': 'Indexação de ficheiros em background',
        'icon': 'ti-search',
    },
    {
        'id': 'icloud_drive',
        'name': 'iCloud Drive',
        'process': 'bird',
        'launchctl': 'com.apple.bird',
        'desc': 'Sincronização iCloud Drive',
        'icon': 'ti-cloud',
    },
    {
        'id': 'photo_analysis',
        'name': 'Análise de Fotos',
        'process': 'photoanalysisd',
        'launchctl': 'com.apple.photoanalysisd',
        'desc': 'Processamento de fotos em segundo plano',
        'icon': 'ti-photo',
    },
    {
        'id': 'siri_suggestions',
        'name': 'Sugestões Siri',
        'process': 'suggestd',
        'launchctl': 'com.apple.suggestd',
        'desc': 'Sugestões inteligentes em background',
        'icon': 'ti-microphone',
    },
    {
        'id': 'cloudd',
        'name': 'CloudKit Daemon',
        'process': 'cloudd',
        'launchctl': 'com.apple.cloudd',
        'desc': 'Sincronização CloudKit de apps',
        'icon': 'ti-cloud-upload',
    },
    {
        'id': 'knowledge_agent',
        'name': 'Knowledge Agent',
        'process': 'knowledge-agent',
        'launchctl': 'com.apple.knowledge-agent',
        'desc': 'Análise de uso para Siri e Spotlight',
        'icon': 'ti-brain',
    },
]

_WINDOWS_SERVICES = [
    {'id': 'windows_update', 'name': 'Windows Update',     'key': 'wuauserv', 'desc': 'Atualizações automáticas',          'icon': 'ti-refresh'},
    {'id': 'print_spooler',  'name': 'Print Spooler',       'key': 'Spooler',  'desc': 'Impressão em segundo plano',         'icon': 'ti-printer'},
    {'id': 'windows_search', 'name': 'Windows Search',      'key': 'WSearch',  'desc': 'Indexação de ficheiros',             'icon': 'ti-search'},
    {'id': 'sysmain',        'name': 'SysMain (SuperFetch)', 'key': 'SysMain',  'desc': 'Pré-carregamento de aplicativos',    'icon': 'ti-cpu'},
    {'id': 'diagtrack',      'name': 'Telemetria',           'key': 'DiagTrack','desc': 'Diagnóstico e telemetria Microsoft', 'icon': 'ti-chart-bar'},
    {'id': 'fax',            'name': 'Fax',                  'key': 'Fax',      'desc': 'Serviço de fax (geralmente inativo)','icon': 'ti-device-floppy'},
]

# ── Helpers ───────────────────────────────────────────────────────────────────

def _is_running_by_name(process_name: str) -> bool:
    for proc in psutil.process_iter(['name']):
        try:
            if process_name.lower() in proc.info['name'].lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return False


def _win_service_status(key: str) -> str:
    try:
        result = subprocess.run(
            ['sc', 'query', key],
            capture_output=True, text=True, shell=True, timeout=5
        )
        out = result.stdout
        if 'RUNNING' in out:
            return 'running'
        if 'STOPPED' in out:
            return 'stopped'
    except Exception:
        pass
    return 'unknown'

# ── Public API ────────────────────────────────────────────────────────────────

def get_services() -> list:
    if _system == 'Darwin':
        out = []
        for s in _MACOS_SERVICES:
            running = _is_running_by_name(s['process'])
            out.append({
                'id':      s['id'],
                'name':    s['name'],
                'desc':    s['desc'],
                'icon':    s['icon'],
                'running': running,
                'status':  'Em execução' if running else 'Parado',
            })
        return out

    if _system == 'Windows':
        out = []
        for s in _WINDOWS_SERVICES:
            status = _win_service_status(s['key'])
            out.append({
                'id':      s['id'],
                'name':    s['name'],
                'desc':    s['desc'],
                'icon':    s['icon'],
                'key':     s['key'],
                'running': status == 'running',
                'status':  'Em execução' if status == 'running' else 'Parado',
            })
        return out

    return []


def stop_service(service_id: str) -> dict:
    if _system == 'Darwin':
        svc = next((s for s in _MACOS_SERVICES if s['id'] == service_id), None)
        if not svc:
            return {'success': False, 'message': 'Serviço não encontrado.'}
        killed = False
        for proc in psutil.process_iter(['name']):
            try:
                if svc['process'].lower() in proc.name().lower():
                    proc.terminate()
                    killed = True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        if killed:
            return {'success': True, 'message': f'"{svc["name"]}" pausado com sucesso.'}
        return {'success': False, 'message': f'"{svc["name"]}" não estava em execução.'}

    if _system == 'Windows':
        svc = next((s for s in _WINDOWS_SERVICES if s['id'] == service_id), None)
        if not svc:
            return {'success': False, 'message': 'Serviço não encontrado.'}
        try:
            result = subprocess.run(
                ['sc', 'stop', svc['key']],
                capture_output=True, text=True, shell=True, timeout=10
            )
            if 'STOP_PENDING' in result.stdout or 'STOPPED' in result.stdout:
                return {'success': True, 'message': f'"{svc["name"]}" parado com sucesso.'}
            return {'success': False, 'message': f'Não foi possível parar "{svc["name"]}". Execute como Administrador.'}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    return {'success': False, 'message': 'Plataforma não suportada.'}
