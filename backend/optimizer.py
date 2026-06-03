from backend import processes as proc_mod
from backend import services as svc_mod
from backend import cleanup as clean_mod
from backend import history


def _fmt(b: int) -> str:
    if b >= 1024 ** 3:
        return f'{b / (1024 ** 3):.1f} GB'
    if b >= 1024 ** 2:
        return f'{b / (1024 ** 2):.0f} MB'
    return f'{b / 1024:.0f} KB'


def get_preview(mode: str = 'gaming') -> dict:
    """
    Returns what the optimizer WOULD do without executing anything.
    Used to populate the pre-optimization modal.
    """
    # Heavy processes (top 6 by resource weight)
    all_procs  = proc_mod.get_processes(30)
    heavy      = [p for p in all_procs if p['cpu'] > 3 or p['ram_bytes'] > 100 * 1024 * 1024]
    heavy      = sorted(heavy, key=lambda p: p['ram_bytes'], reverse=True)[:6]

    # Running services
    all_svcs   = svc_mod.get_services()
    running    = [s for s in all_svcs if s['running']]

    # Cleanable items
    clean_items = clean_mod.get_cleanable_items()

    est_ram  = sum(p['ram_bytes'] for p in heavy)
    est_disk = sum(c['size_bytes'] for c in clean_items)

    return {
        'mode':                  mode,
        'processes':             heavy,
        'services':              running,
        'cleanup':               clean_items,
        'estimated_ram_label':   _fmt(est_ram),
        'estimated_disk_label':  _fmt(est_disk),
        'estimated_ram_bytes':   est_ram,
        'estimated_disk_bytes':  est_disk,
    }


def run(plan: dict) -> dict:
    """
    Execute the optimization plan selected by the user in the modal.

    plan = {
        'mode':             'gaming',
        'kill_pids':        [1234, 5678],
        'stop_service_ids': ['spotlight', 'icloud_drive'],
        'clean_item_ids':   ['user_caches', 'trash'],
    }
    """
    killed, stopped, cleaned, errors = [], [], [], []
    freed_disk = 0

    for pid in plan.get('kill_pids', []):
        r = proc_mod.kill_process(int(pid))
        (killed if r['success'] else errors).append(r['message'])

    for svc_id in plan.get('stop_service_ids', []):
        r = svc_mod.stop_service(svc_id)
        (stopped if r['success'] else errors).append(r['message'])

    for item_id in plan.get('clean_item_ids', []):
        r = clean_mod.clean_item(item_id)
        if r['success']:
            cleaned.append(r['message'])
            freed_disk += r.get('freed_bytes', 0)
        else:
            errors.append(r['message'])

    mode = plan.get('mode', 'custom')

    # Persist to history
    history.add({
        'mode':             mode,
        'summary':          (
            f'{len(killed)} processo(s) encerrado(s) · '
            f'{len(stopped)} serviço(s) pausado(s) · '
            f'{len(cleaned)} item(s) limpo(s)'
        ),
        'killed':           len(killed),
        'stopped':          len(stopped),
        'cleaned':          len(cleaned),
        'freed_disk_label': _fmt(freed_disk),
    })

    return {
        'killed':           killed,
        'stopped':          stopped,
        'cleaned':          cleaned,
        'errors':           errors,
        'freed_disk_label': _fmt(freed_disk),
    }
